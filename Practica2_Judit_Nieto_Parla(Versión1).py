"""
@author: Judit Nieto Parla
"""
#VERSIÓN 1

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 30
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.cars_north = Value('i', 0)
        self.cars_south = Value('i', 0)
        self.pedestrian = Value('i', 0)
        self.dentro_norte = Value('i',0)
        self.dentro_sur = Value ('i',0)
        self.dentro_peaton = Value('i',0)
        self.abierto_norte = Condition(self.mutex)
        self.abierto_sur = Condition(self.mutex)
        self.abierto_peaton = Condition (self.mutex)
    
    def adelante_coches_norte(self):
        return self.dentro_sur.value==0 and self.dentro_peaton.value==0
    
    def adelante_coches_sur (self):
        return self.dentro_norte.value==0 and self.dentro_peaton.value==0
    
    def adelante_peaton (self):
        return self.dentro_norte.value==0 and self.dentro_sur.value==0
    
    
    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        if direction==SOUTH: 
            self.cars_south.value+=1
            self.abierto_sur.wait_for(self.adelante_coches_sur)
            self.dentro_sur.value+=1
            self.cars_south.value-=1     
        if direction==NORTH:
            self.cars_north.value+=1
            self.abierto_norte.wait_for(self.adelante_coches_norte)
            self.dentro_norte.value+=1
            self.cars_north.value-=1
        self.mutex.release()
        
    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire()
        if direction==SOUTH:
            self.dentro_sur.value-=1
            if self.dentro_sur.value==0:
                self.abierto_norte.notify_all()
                if self.dentro_norte.value==0:
                    self.abierto_peaton.notify_all()
        if direction==NORTH:
            self.dentro_norte.value-=1
            if self.dentro_norte.value==0:
                self.abierto_sur.notify_all()
                if self.dentro_sur.value==0:
                    self.abierto_peaton.notify_all()
        self.mutex.release()
        
    def wants_enter_pedestrian (self):
        self.mutex.acquire()
        self.pedestrian.value+=1
        self.abierto_peaton.wait_for(self.adelante_peaton)
        self.pedestrian.value-=1
        self.dentro_peaton.value+=1
        self.mutex.release()
        
    def leaves_pedestrian(self):
        self.mutex.acquire()
        self.dentro_peaton.value-=1
        if self.dentro_peaton.value==0:
            self.abierto_sur.notify_all()
            self.abierto_norte.notify_all()
        self.mutex.release()
    
    def __repr__(self) -> str:
        return f'Monitor:{self.dentro_norte.value}, {self.dentro_sur.value},{self.dentro_peaton.value}'
    
    
def delay_car_north() -> None:
    delay_time = random.uniform(*TIME_IN_BRIDGE_CARS)
    print(f"car heading north entering bridge delay {delay_time} s.")
    time.sleep(delay_time)

def delay_car_south() -> None:
    delay_time = random.uniform(*TIME_IN_BRIDGE_CARS)
    print(f"car heading south entering bridge delay {delay_time} s.")
    time.sleep(delay_time)

def delay_pedestrian() -> None:
    delay_time = random.uniform(*TIME_IN_BRIDGE_PEDESTRIAN)
    print(f"pedestrian entering bridge delay {delay_time} s.")
    time.sleep(delay_time)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_north.start()    
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gcars_south.start()
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()





