# Modules

Runtime modules are implemented as dynamic libraries that are loaded as needed.  The model loaded determines whether a runtime module is needed by specifying a [[module]] block.

**Prior to Version 2.0** : Adding a module in Windows can be done using the "Add GridLAB module" wizard.  In Linux it can be done using the "add_gridlab_module" script. 	This document is provided for completeness and to provide details that may be necessary should the scripts not function as required.

**As of Version 4.3** : The [module template](https://arras.energy/module_template) should be used to build new modules. The template is designed to build external modules. However, the source code to an external module is the same as for an internal module.

The exact approach to use in building a GridLAB module is not clear cut. In general a module is a solver that can compute the steady state of a collection of objects given a specific boundary condition.  For example, a power flow solver makes sense as a module because the steady state of a flow network can be directly computed.  However, a market clearing system and a load simulation doesn't make sense because the market is  influenced not only by demand from loads, but also by supply.  As a general rule, if a set of simultaneous equations can be solved to obtain the state of a system, the system is suitable for implementation as a module.

Modules must be able to implement a least three capabilities:
* they must be able to create objects on demand (see `create()`)
* they must be able to initialize objects on demand (see `init()`)
* they must be able to compute the state of individual objects at a specified date and time on demand (see `sync()`)

In addition, modules generally should be able to implement the following

* compute the states of objects with some degree of parallelism
* load and save data in various exchange formats
* inform the GridLAB-D core which objects data members are exposed to other modules
* handle notification events of data members about to be changed or just changed
* determine whether an object is a subtype of another object
* verify that a collection of objects form a self-consistent and correct model

It turns out that implementing these capabilities is not as easy as it at first seems.  In particular, the synchronization has typically been one of the most challenging concepts for programmers to understand.  Given the amount of time spent in sync calls, it is recommended that considerable time and effort be put into its design.

## Basic Synchronization

An object's sync method actually performs two essential functions. First, it updates the state of an object to a designated point in time, and second it lets the core know when the object is next expected to change state. This is vital for the core to know because the core's clock will be advanced to the time of the next expected state change, and all objects will be synchronized to that time.

In general a sync() function should be aware of three time values:
* $t_0$ is the time from which the object is being advanced.  This is not the current time, because it is presumed that the object has not yet advanced to the current time and this is why `sync()` is being called.
* $t_1$ is the time to which the object is being advanced.  Think of this as `now` from the object's perspective. This is usually the current time from the core's perspective (but don't assume it always is).
* $t_2$ is the time at which the object expects to have its next state change.  This time must be computed by the object during or immediately after the state is advanced to $t_1$.  This is the time returned to the core should the `sync()` call succeed.

If no state change is ever anticipated then $t_2 = \mathrm{TS_NEVER}$ is returned, indicating that barring any changes to its boundary condition, the object is in steady state.

If an object's `sync()` method determines that the object is not yet in steady state (i.e., the module has not converged), then $t_2 = t_1$ is returned.

If an object's `sync()` method determines that it cannot update to $t_1$ as required, the simulation has failed. It can either throw an exception using `GL_THROW()` or return $t_2 \le t_1$ to indicate the time at which the problem is believed to have occurred.

The time window $t_1 - t_0$ is the past window and the `sync()` method must implement all behaviors during that time as though they have already occurred.

The time window $t_2 - t_1$ is the future window and the sync function must not implement behaviors in this window yet, as they have not yet occurred.

It is a non-trivial fact that if all objects in all modules in GridLAB model return $t_2 = \mathrm{TS\_NEVER}$, then the simulation stops successfully.  This is because the system has completely settle to a steady state and there is nothing further to compute.

For more details on synchronization in GridLAB-D see [[/User_manual/1_-_Introduction/2_-_Theory_of_Operation]].

## Control Code

One very important aspect of synchronization behavior is how control code is handled when object behavior goes beyond the mere physics of its response to its boundary condition.  It is quite easy to implement control code that is integrated with the physical model.  However, this would prevent users from altering the control code without altering the source code of the object's implementation.

**Prior to Version 3.0** : To address this problem, objects can implement default control code that is disabled if a [[PLC]] object is attached later.  The ability to alter control code should be made available when implemented for any object for which this is a realistic possibility, which is very nearly always.

To implement default machine [[PLC]] code for an object, the module must expose a ''plc''() method that will be called immediately before ''sync''() is called, but only if not external PLC method is provided in the model.  This ''plc''() method may be written as though it was integrated with the physics implemented in ''sync''(), but the physics must be able to update even when the default [[PLC]] code is not run.

**As of Version 3.0** : As of Version 3.0 the PLC module will no longer be supported and the [[PID controller]] module replaces it.  Alternatively, the [[class]] [[class#intrinsic|intrinsic]] function [[class#plc|plc]] supports simple control code replacements.

## Building a GridLAB module

A GridLAB module must be a Windows DLL or a Linux SO.

### MS Windows

Windows is not supported directly as of Version 4.3.

### macOS/ and Linux makefiles

* `module/Makefile.mk`: You must add the module's makefile to the `module` folder's general Makefile.

### Event Handlers

The following event handlers can be implemented.

* **create()** (required)

    EXPORT_CREATE(my_class);

* **init()** (required)
  
    EXPORT_INIT(my_class);

* **precommit()**
    EXPORT_PRECOMMIT(my_class);
* **sync()**
    EXPORT_SYNC(my_class);
* **commit()**
    EXPORT_COMMIT(my_class);
* **finalize()**
    EXPORT_FINALIZE(my_class);
* **isa()**
    EXPORT_ISA(my_class);
* **notify()**
    EXPORT_NOTIFY(my_class);
* **plc()** (obsolete)
    EXPORT_PLC(my_class);
* **recalc()**
    EXPORT_RECALC(my_class);

## Debugging lock timeouts

A maximum spin timeout is implemented in both read and write locks to prevent deadlocks. If you run into a situation where you get a "write lock timeout" or "read lock timeout" then most likely you've encountered a condition where an object is trying to take a lock out on itself.  Consider the following

* _Are you using a locking accessor in a sync call on an autolocked object?_
  If so, consider using direct access call instead because the object is already locked by the core.

* _Is the object locked for a very long time because it's doing something that really does take a long time?_
  If so, you may have to increase the value of '''MAXSPIN''' in the <tt>core/lock.cpp</tt>. Note that this value has a maximum of about 4e9 and it is currently set to 1e9 (which is roughly 10 seconds), so there's not much room left for growth.  If this is a problem, please file a ticket and an alternate timeout method will have to be implemented.

* Try debugging with a breakpoint on the <tt>throw_exception</tt> calls in <tt>core/lock.cpp</tt>.
  This should tell you exactly which lock is causing the timeout.
