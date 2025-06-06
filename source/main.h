/*	File: main.h 
 	
 	Copyright (C) 2008, Battelle Memorial Institute
 */

#ifndef _MAIN_H
#define _MAIN_H

#if ! defined _GLDCORE_H && ! defined _GRIDLABD_H
#error "this header may only be included from gldcore.h or gridlabd.h"
#endif

#include "globals.h"
#include "exec.h"
#include "cmdarg.h"
#include "gui.h"

#include <list>
#include <sys/wait.h>

/*	Typedef: EXITCALL */
typedef int (*EXITCALL)(int);

struct s_pipes {
	FILE *child_input;
	FILE *child_output;
	FILE *child_error;
	char *child_command;
	pid_t child_pid;
};
struct s_pipes *popens(const char *program, FILE **input, FILE **output, FILE **error);
int ppolls(struct s_pipes *pipes, FILE* input_stream, FILE* output_stream, FILE *error_stream);
int ppolls(struct s_pipes *pipes, char *output_buffer, size_t output_size, FILE *error_stream);
int pcloses(struct s_pipes *pipes, bool wait=true);
#define READ_END 0
#define WRITE_END 1

class onexitcommand {
private:
	int exitcode;
	const char *command;
public:
	inline onexitcommand(int xc, const char *cmd)
	{
		exitcode = xc;
		command = strdup(cmd);
	};
	inline ~onexitcommand(void)
	{
		free((void*)command);
	}
	inline int get_exitcode(void) 
	{ 
		return exitcode; 
	};
	inline const char * get_command(void)
	{
		return command;
	};
	inline int run(void)
	{
		SET_MYCONTEXT(DMC_MAIN)
		int rc = system(command);
		IN_MYCONTEXT output_debug("onexitcommand(xc=%d,cmd='%s').run() --> exit code %d",exitcode,command,rc);
		return rc;
	};
};

/*	Class: GldMain
	The GldMain class implement an instance of a GridLAB-D simulation.
 */
class GldMain {
private: // private variables
	std::list<onexitcommand> exitcommands;
	std::list<EXITCALL> exitcalls;
private: // instance variables
	GldGlobals globals;
	GldExec exec;
	GldCmdarg cmdarg;
	GldGui gui;
	GldLoader loader;
public: // public variables
	LOCKVAR rlock_count;
	LOCKVAR rlock_spin;
	LOCKVAR wlock_count;
	LOCKVAR wlock_spin;
public:
	/*	Method: get_globals
		This function returns a reference to the global variable list of the instance.
	 */
	inline GldGlobals *get_globals() { return &globals; };

	/*	Method: get_exec
		This function returns a reference to the execution control of the instance.
	 */
	inline GldExec *get_exec() { return &exec; };

	/*	Method: get_cmdarg
		This function returns a reference to the command line processor of the instance
	 */
	inline GldCmdarg *get_cmdarg() { return &cmdarg; };

	/* Method: get_gui
		This function returns a reference to the GUI implementation
	 */
	inline GldGui *get_gui() { return &gui; };

	/* Method: get_loader
		This function returns a reference the the loader implementation
	 */
	inline GldLoader *get_loader() { return &loader; };

private:
	static unsigned int next_id; // next instance id
	unsigned int id; // this instance id
	time_t starttime; // wallclock start time of this simulation

public:		
	/*	Constructor: GldMain
	 */
	GldMain(int argc = 0, const char *argv[] = NULL);

	//	Destructor: GldMain
	~GldMain(void);

	/*	Method: pause_at_exit
		This function causes the main program to pause when exit() is called.  
		The message "Press [RETURN] to exit... " is displayed and the user must
		hit return for the program to complete the exit() call.
	 */
	static void pause_at_exit(void);

	/*	Method: mainloop
		This function begins processing the main loop of GridLAB-D using the command
		argument provided.
		The return value is the standard exit code.
		See also: <
	 */
	int mainloop(int argc = 0, const char *argv[] = NULL);

	/* 	Method: add_on_exit
		Adds a command to be executed on exit of main
	 */
	int add_on_exit(int xc, const char *cmd);
	int add_on_exit(EXITCALL call);

	/*	Method: run_on_exit
		Runs the on-exit command list for the exit code given
		Returns: exit code of first failed call, or 0 if all calls succeeded
	 */
	int run_on_exit(int return_code = 0);

private:	// private methods
	void set_global_browser(const char *path = NULL);
	void set_global_execname(const char *path);
	void set_global_execdir(const char *path);
	void set_global_command_line(int argc = 0, const char *argv[] = NULL);
	void set_global_workdir(const char *path = NULL);
	void create_pidfile(void);
	static void delete_pidfile(void);

public: 

	// Method: get_id()
	inline pid_t get_id() { return id; }

	// Method: dump
	inline void dump(void) { return globals.dump();};

	// Method: remote_read
	inline void *remote_read(void *local, GLOBALVAR *var) { return globals.remote_read(local,var);};

	// Method: remote_write
	inline void remote_write(void *local, GLOBALVAR *var) { return globals.remote_write(local,var);};

	// Method: global_saveall
	inline size_t global_saveall(FILE *fp) { return globals.saveall(fp);};

public:

	// Section: Loader access
	inline bool load_file(const char *filename) { return loader.load(filename); };

public:

	// Section: Globals variable access

	// Method: global_init
	inline STATUS global_init(void) { return globals.init();};

	// Method: global_getfirst
	inline GLOBALVAR *global_getfirst(void) { return globals.getnext(NULL);};

	// Method: global_getnext
	inline GLOBALVAR *global_getnext(const GLOBALVAR *var) { return globals.getnext(var);};

	// Method: global_find
	inline GLOBALVAR *global_find(const char *name) { return globals.find(name);};

	// Method: global_create
	inline GLOBALVAR *global_create(const char *name, ...) { va_list ptr; va_start(ptr,name); GLOBALVAR *var = globals.create_v(name,ptr); va_end(ptr); return var;};

	// Method: global_setvar
	inline STATUS global_setvar(char *def,...) { va_list ptr; va_start(ptr,def); STATUS res = globals.setvar_v(def,ptr); va_end(ptr); return res;};

	// Method: global_getvar
	inline const char *global_getvar(const char *name, char *buffer, size_t size) { return globals.getvar(name,buffer,size);};

	// Method: global_isdefined
	inline bool global_isdefined(const char *name) { return globals.isdefined(name);};

	// Method: global_dump
	inline void global_dump(void) { return globals.dump();};

	// Method: global_getcount
	inline size_t global_getcount(void) { return globals.getcount();};

	// Method: global_restore
	inline void global_restore(GLOBALVAR *pos) { return globals.restore(pos);};

	// Method: global_push
	inline void global_push(char *name, char *value) { return globals.push(name,value);};

	/* 	Method: subcommand
		Run the subcommand in the current environment, redirecting output to stdout/stderr.
		Returns:
		-1	failed to start command
		>=0 command exit code
	 */
	int subcommand(const char *format,...);

	// Method: check_runtime
	bool check_runtime(bool use_exception=false);
};

DEPRECATED extern GldMain *my_instance; // TODO: move this into main() to make system globally reentrant

#endif