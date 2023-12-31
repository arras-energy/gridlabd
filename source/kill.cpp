/** kill.cpp
	Copyright (C) 2008 Battelle Memorial Institute

   @file kill.cpp
   @addtogroup exec
   This program provide the same kill functionality that is available to Linux versions

 @{
 **/

#ifdef WIN32

#include "gldcore.h"

/* KILLONLY is undefined when building the kill program, 
   and defined when compiling with the main GridLAB-D 
   core modules
 */
#ifndef KILLONLY

#include "gridlabd.h"

static int handler_stop = 0;
void kill_stophandler(void)
{
	handler_stop = 1;
}

void msghandler(void *param)
{
	char name[32];
	HANDLE hEvent;
	unsigned int sig = (unsigned int)(int64)param;
	pid_t pid = (pid_t)_getpid();
	snprintf(name,sizeof(name)-1,"gridlabd.%u.%u",pid,sig);
	hEvent = CreateEventA(NULL,TRUE,FALSE,name);
	output_verbose("creating gridlabd signal handler %u for process %u",sig,pid);
	while (WaitForSingleObject(hEvent,INFINITE)==WAIT_OBJECT_0)
	{
		output_verbose("windows signal handler activated");
		raise(sig);
		ResetEvent(hEvent);
	}
}

void kill_starthandler(void)
{
	if (_beginthread(&msghandler, 0, (void*)SIGINT)==1 || _beginthread(&msghandler, 0, (void*)SIGTERM)==1)
		output_error("kill handler failed to start");
	else
		output_verbose("windows message signal handlers started");
}
#else
#define output_error printf
#define output_verbose
#endif

/** Send a kill signal to a windows version of GridLAB-D
    @return 0 on successfull completion, -1 on error (e.g., no such signal, no such process)
 **/
int kill(pid_t pid,	/**< the window process id */
		 int sig)				/**< the signal id (see signal.h) */
{
	char name[32];
	HANDLE hEvent;
	snprintf(name,sizeof(name)-1,"gridlabd.%u.%u",pid,sig==0?SIGINT:sig); /* use INT for sig==0 just to check */
	hEvent = OpenEventA(EVENT_MODIFY_STATE,FALSE,name);
	
	/* existence check only */
	if ( sig==0 )
	{
		if ( hEvent!=NULL )
		{
			CloseHandle(hEvent);
			return 0;
		}
		else
		{
			errno = ESRCH;
			return -1;
		}
	}

	/* valid signal needs to be sent */
	else if (hEvent==NULL)
	{
		errno = EINVAL; // TODO distinguish between bad signal and bad pid
		output_error("unable to signal gridlabd process %d with signal %d (error %d)", pid, sig, GetLastError());
		return -1;
	}
	else 
	{
		SetEvent(hEvent);
		output_verbose("signal %d sent to gridlabd process %d", sig, pid);
		CloseHandle(hEvent);
		return 0;
	}
}
#endif

/** @} */
