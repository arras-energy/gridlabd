// module/behavior/learning.cpp
// Copyright (C) 2024 Regents of the Leland Stanford Junior University

#include "behavior.h"

EXPORT_CREATE(learning);
EXPORT_INIT(learning);
EXPORT_PRECOMMIT(learning);
EXPORT_COMMIT(learning);
EXPORT_METHOD(learning,target);
EXPORT_METHOD(learning,policy);
EXPORT_METHOD(learning,reward);

CLASS *learning::oclass = NULL;
class learning *learning::defaults = NULL;

learning::learning(MODULE *module)
{
	if (oclass==NULL)
	{
		// register to receive notice for first top down. bottom up, and second top down synchronizations
		oclass = gld_class::create(module,"learning",sizeof(learning),PC_AUTOLOCK|PC_OBSERVER);
		if (oclass==NULL)
			throw "unable to register class learning";
		else
			oclass->trl = TRL_PROVEN;

		defaults = this;
		if (gl_publish_variable(oclass,

			PT_method, "target", get_target_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "Target CLASS:PROPERTY or OBJECT.PROPERTY",

			PT_method, "policy", get_policy_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "Learning policy",

			PT_double, "exploration", get_exploration_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "Exploration factor (1-exploitation factor)",

			PT_double, "interval[s]", get_interval_offset(),
				PT_REQUIRED,
				PT_DESCRIPTION, "Interval of decision-making",

			PT_double, "discount", get_discount_offset(),
				PT_DESCRIPTION, "Discount rate of future rewards (per interval)",

			PT_method, "reward", get_reward_offset(),
				PT_OUTPUT,
				PT_DESCRIPTION, "Observed rewards for each state",

			NULL)<1)
		{
				throw "unable to publish learning properties";
		}
	}
}

int learning::create(void) 
{
	return 1; // return 1 on success, 0 on failure
}

int learning::init(OBJECT *parent)
{
	return 1; // return 1 on success, 0 on failure, 2 on retry later
}

TIMESTAMP learning::precommit(TIMESTAMP t0)
{
	return TS_NEVER;
}

TIMESTAMP learning::commit(TIMESTAMP t0, TIMESTAMP t1)
{
	return TS_NEVER;
}

int learning::target(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// calculate size of result
		return 0;
	}
	else if ( len == 0 )
	{
		// read result from buffer
		return strlen(buffer);
	}
	else
	{
		// write result into buffer
		return 0;
	}
}

int learning::policy(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// calculate size of result
		return 0;
	}
	else if ( len == 0 )
	{
		// read result from buffer
		return strlen(buffer);
	}
	else
	{
		// write result into buffer
		return 0;
	}
}

int learning::reward(char *buffer, size_t len)
{
	if ( buffer == NULL )
	{
		// calculate size of result
		return 0;
	}
	else if ( len == 0 )
	{
		// read result from buffer
		return strlen(buffer);
	}
	else
	{
		// write result into buffer
		return 0;
	}
}
