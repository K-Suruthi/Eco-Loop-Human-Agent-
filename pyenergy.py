import sys

sys.path.append(r"C:\EnergyPlusV26-1-0")

from pyenergyplus.api import EnergyPlusAPI

api = EnergyPlusAPI()
print("EnergyPlus API loaded successfully!")