import time

from position import (
    position,  # Replace with the actual module name where position class is defined
)
from sortedcontainers import SortedDict


# Define margin function if needed
def margin_function(side, price):
    # Your margin function implementation
    pass


# Initialize position
pos = position([lambda x: x, lambda x: 100 - x], [0, 0], [1000000, 0])

# Execute actions repeatedly with timing
iterations = 1000  # Change this to how many times you want to run

start_time = time.time()

for i in range(iterations):
    pos.add_order(40, 0, 50)
    pos.add_order(35, 0, 50)
    pos.add_order(50, 1, 50)
    pos.add_order(55, 1, 50)
    pos.fill_order(40, 0, 40, 25)
    pos.fill_order(50, 1, 50, 30)
    pos.fill_order(40, 0, 40, 25)
    pos.fill_order(35, 0, 35, 50)
    pos.fill_order(50, 1, 50, 20)
    pos.fill_order(55, 1, 55, 50)


pos.debug()

end_time = time.time()

total_time = end_time - start_time
print(f"Total time for {iterations} iterations: {total_time:.4f} seconds")
print(f"Average time per iteration: {(total_time / iterations) * 1000:.2f} ms")
