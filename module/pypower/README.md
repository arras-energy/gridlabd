This module was developed by [David Chassin](https://github.com/dchassin) at SLAC National Accelerator Laboratory as part of the REGROW project (see https://github.com/slacgismo/regrow).

# Theory of Operation

The `pypower` module provides PF and OPF solvers that are suitable for reduced-order modeling of transmission and substransmission systems.  The solvers are integrated at the module level, meaning that module event handlers initiate the powerflow solvers. The two events that are handled are the `on_init` and `on_sync` events.  In addition class-level event handlers are implemented as follows.

| Class | `create` | `init` | `precommit` | `presync` | `sync` | `postsync` | `commit` |
| ----- | :------: | :----: | :---------: | :-------: | :----: | :--------: | :------: |
| Module | X       | X      |             |           | X [1]  |            |          | 
| `branch` | X     | X      |             |           |        |            |          |
| `bus` | X        | X      |             | X         |        |            |          |
| `gen` | X        | X      |             |           |        |            |          |
| `gencost` | X    | X      |             |           |        |            |          |
| `load` | X       | X      |             | X         | X      | X          |          |
| `powerline` | X  | X      | X           |           |        |            |          |
| `powerplant` | X | X      |             | X         | X      | X          |          |

[1] Only called when `on_sync(data)` is defined in `controllers` python file. 

# Modeling

The model has three layers.

1. Solver layer (`bus`, `branch`, `gen`, and `gencost` classes) which are used to transfer data from the model to solver data arrays.
2. Model layer (`powerplant`, `powerline`, and `load` classes) which are used to implement model reductions from detailed system models to solver data.
3. Control layer (`controllers` python file) which are used to implement controls for specific model reductions classes.

Data transfer from control layer to model layer are performed by passing object data to control functions defined in the `controllers` python file and copying returned values back to the model layer objects. Data transfer from the model layer to the solver layer is performed automatically by the `on_sync` solver code. Some model data is not copied unless the OPF solver is enabled and `gencost` objects are defined.

![Module structure diagram](https://lucid.app/publicSegments/view/93b52ed0-f566-4cdc-ab3d-345b52b3e2ce/image.png) 

Figure 1: Module structure diagram [[Edit](https://lucid.app/lucidspark/56584160-b3c6-4798-9558-ce9f991d4ce0/edit?viewport_loc=-701%2C54%2C3413%2C1701%2C0_0&invitationId=inv_66ba35f7-3f3c-4b15-8cde-31ac0933cf77)]

# Control

The `controllers` file may contain the following functions

* `on_init()` which is called when the model is initialized at the start time of the simulation.
* `on_sync(data)` which is called when the timestep is advanced to the next simulation step. The `data` object contains the data which will be sent to the solver. This data may be changed. Caveat: this can seriously mess up the solver and cause it fail.
* `my_controller(obj,**kwargs)` which is called for any `load` or `powerplant` object which defines its `controller` property with the corresponding function name.  The value `obj` contains the name of the object and `kwargs` contains a `dict` of the objects properties. The return value is a `dict` which can contain any property to be copied back to the object, as well as a time `t` at which the next event occurs, if any.
