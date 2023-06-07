# Campaigner

An API to manage campaigns from all the different channels under one roof

## How to run?
Project is in the form of a Python module, with dependencies and startup managed with pdm

### Installing dependencies
```python
pip install pdm
```

### Running the module
From the project directory, invoke
```python
python -m campaigner
```

## Track progress
- [x] Create a view class for the requests
- [x] Create the two routes
- [x] Fetch details of a userid from settings table
- [x] <b> Check for Race Conditions </b>
- [x] Create a table campaigner
- [x] If data for priority exists in settings, update from 
- [x] Implemented scheduling
- [x] Implement Failsafe
- [x] Add logic to check for thread kill along with thread sleep
- [x] Add a status route for controlling the processes
- [ ] Incorporate the various APIs

## PLEASE NOTE

This code is part of Tubelight Communications.

**Unauthorized commercial usage is prohibited.**

Licensed under [CC BY-NC-ND 4.0](LICENSE.md).