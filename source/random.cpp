/** random.cpp
	Copyright (C) 2008 Battelle Memorial Institute
	@file random.c
	@addtogroup random Random number generators
	@ingroup core
	
	Generate random numbers according to various distributions.

	@note The random number generators are not thread-safe.  This isn't generally
	a problem, unless you are using the pseudo-random sequences.  In that case, you
	need to lock the state variable you are using when generating random numbers.

 @{
 **/

#include "gldcore.h"

SET_MYCONTEXT(DMC_RANDOM)

#ifdef WIN32
#define isfinite _finite
#include <process.h>
#define getpid _getpid
#else
#include <unistd.h>
#endif

static LOCKVAR random_lock=0;

#ifdef __MINGW32__
inline char* strtok_t(char *str, const char *delim, char **nextp)
{
    char *ret;

    if (str == NULL)
    {
        str = *nextp;
    }

    str += strspn(str, delim);

    if (*str == '\0')
    {
        return NULL;
    }

    ret = str;

    str += strcspn(str, delim);

    if (*str)
    {
        *str++ = '\0';
    }

    *nextp = str;

    return ret;
} 

#define strtok_s strtok_t
#endif

static unsigned int *ur_state = NULL;

unsigned entropy_source(void)
{
	struct timeval t;
	gettimeofday(&t,NULL);
	return (unsigned)(getpid()*t.tv_usec);
}

void random_init(const char *name,const char *value)
{
	/* randomizes the random number generator start value */
	if ( global_randomseed == 0 )
	{
		global_randomstate = global_randomseed = entropy_source();
	}
	else if ( global_randomstate == 0 )
	{
		global_randomstate = global_randomseed;
	}

	srand(1);
	ur_state = &global_randomstate;
}

/** Converts a distribution name to a #RANDOMTYPE
 **/
static struct s_distributions {
	const char *name;
	RANDOMTYPE type;
	int nargs;
} map[] = {
	/* tested */
	{"degenerate", RT_DEGENERATE,1},
	{"uniform",RT_UNIFORM,2},
	{"normal",RT_NORMAL,2},
	{"bernoulli",RT_BERNOULLI,1},
	{"sampled",RT_SAMPLED,-1},
	{"pareto",RT_PARETO,2},
	{"lognormal",RT_LOGNORMAL,2},
	{"exponential",RT_EXPONENTIAL,1},
	{"rayleigh",RT_RAYLEIGH,1},
	/* untested */
	{"weibull",RT_WEIBULL,2},
	{"gamma",RT_GAMMA,1},
	{"beta",RT_BETA,2},
	{"triangle",RT_TRIANGLE,2},
	/** @todo Add some other distributions (e.g., Cauchy, Laplace)  (ticket #56)*/
};
/** Converts a distribution name to a #RANDOMTYPE
 **/
RANDOMTYPE random_type(const char *name) /**< the name of the distribution */
{
	for (struct s_distributions *p=map; p<map+sizeof(map)/sizeof(map[0]); p++)
	{
		if (strcmp(p->name,name)==0)
			return p->type;
	}
	return RT_INVALID;
}
/** Gets the number of arguments required by distribution (0=failed, -1=variable)
 **/
int random_nargs(const char *name)
{
	for (struct s_distributions *p=map; p<map+sizeof(map)/sizeof(map[0]); p++)
	{
		if (strcmp(p->name,name)==0)
			return p->nargs;
	}
	return 0;
}

bool random_from_string(const char *str, double *value)
{
	// parse input string
	char name[64];
	char args[1024];
	if ( sscanf(str,"%63[a-z](%1023[^)])",name,args) != 2 )
	{
		output_error("random_from_string(str='%s'): distribution syntax is invalid",str,name);
		return false;
	}

	// get distribution type
	RANDOMTYPE type = random_type(name);
	if ( type == RT_INVALID )
	{
		output_error("random_from_string(str='%s'): distribution type '%s' is not valid",str,name);
		return false;
	}

	// get arguments
	double argv[1024];
	unsigned int n = 0;
	char *last = NULL;
	char *next = NULL;
	while ( ( next = strtok_r(next?NULL:args,",",&last) ) != NULL && n < sizeof(argv)/sizeof(argv[0]) )
	{
		if ( sscanf(next,"%lf",&argv[n]) == 0 )
		{
			output_error("random_from_string(str='%s'): argument %d is not a valid double",str,n);
			return false;
		}
		n++;
	}
	int nargs = random_nargs(name);
	if ( nargs>0 && (int)n != nargs )
	{
		output_error("random_from_string(str='%s'): incorrect number of arguments for distribution type '%s', expected '%d' but found '%d'",str,name,nargs,n);
		return false;
	}

	// get random value using distribution arguments
	switch ( n )
	{
	case 1:
		*value = random_value(type,NULL,argv[0]);
		return true;
	case 2:
		*value = random_value(type,NULL,argv[0],argv[1]);
		return true;
	default:
		output_error("random_from_string(str='%s'): distributions with more than 2 arguments not supported yet (nargs=%u)",str,n);
		return false;
	}
}

/** randwarn checks to see if non-determinism warning is necessary **/
int randwarn(unsigned int *state)
{
	static int warned=0;
	if (global_nondeterminism_warning && !warned)
	{
		warned=1;
		output_warning("non-deterministic behavior probable--rand was called while running multiple threads");
	}
	
	if ( global_randomnumbergenerator==RNG2 )
	{
		/* use the stdc (RNG2) rand functions */
		if ( state!=NULL )
			srand(*state);
		return rand();
		/* note that RNG2 does not write back the state */
	}
	else if ( global_randomnumbergenerator==RNG3 )
	{
		/* Park-Miller LCG allows very large modulus - this one is use in Cray RANF */
#define MODULUS 281474976710656ULL (2^48)
#define MULTIPLIER 44485709377909ULL
		if ( state==NULL ){
			if(ur_state != NULL){
				state = ur_state;
				*ur_state = (unsigned int)((MULTIPLIER*(unsigned int64)(*ur_state))&0xffffffffffffULL);
				return ((*state)>>16)&0x7fff;
			} else {
				/* stateless - use the OS rng, which keeps its own internal state */
				return rand();
			}
		}

		*state = (unsigned int)((MULTIPLIER*(unsigned int64)(*state))&0xffffffffffffULL); /* %2^48 same as &(2^48-1) */
		/* state is truncated to 2^32 */
		return ((*state)>>16)&0x7fff;
		/* note that RNG3 writes back the state */
	}
	else
	{
		/* can't recognize what RNG is selected */
		throw_exception("unknown random number generator selected (global_randomnumbergenerator==%d)", global_randomnumbergenerator);
		return 0;
	}
}

/* generate a random id number */
unsigned int64 random_id(void)
{
	static unsigned int state = 0;
	int64 rv = 0;
	if ( state==0 ) state = (unsigned int)time(NULL);	
	rv = randwarn(&state);
	rv = (rv<<15) ^ randwarn(&state);
	rv = (rv<<15) ^ randwarn(&state);
	rv = (rv<<15) ^ randwarn(&state);
	rv = (rv<<3) ^ randwarn(&state);
	if(rv < 0){
		return -rv;
	}
	return rv;
}

/* generate a random key */
void random_key(unsigned long long *ptr, size_t len)
{
	static unsigned int state = 0;
	if ( state == 0 ) state = (unsigned int)time(NULL);
	while ( len-- > 0 )
	{
		unsigned int64 rv = 0;
		rv = randwarn(&state);
		rv = (rv<<15) ^ randwarn(&state);
		rv = (rv<<15) ^ randwarn(&state);
		rv = (rv<<15) ^ randwarn(&state);
		rv = (rv<<3) ^ randwarn(&state);
		*ptr++ = rv;
	}
}

/* uniform distribution in range (0,1( */
double randunit(unsigned int *state)
{
	double u;
	unsigned int ur;

	if ( state==NULL || state==ur_state )
	{
		state=ur_state;
		wlock(&random_lock);
	}

TryAgain:
	ur = randwarn(state);
	if (state!=NULL && global_randomnumbergenerator==RNG2 )
		*state = ur;
	u = ur/(0x7fff+1.0);
	if ( u<=0 || u>=1 ){
		if( state!=0 && *state == 0){
			*state = randwarn(0);
			output_verbose("randunit() introducing extra randomness to prevent state stagnation and infinite loops");
		}
		goto TryAgain;
	}

	if ( state==ur_state )
		wunlock(&random_lock);
	
	return u;

}
double randunit_pos(unsigned int *state)
{
	double ur = 0.0;
	while (ur<=0)
		ur = randunit(state);
	return ur;
}

/** Generate the same number always.  This is the Dirac delta function:

	The probability density function for the Dirac delta function
	\f[ \varphi\left(a\right) = 1.0 \f]
	
 **/
double random_degenerate(unsigned int *state, double a)
{
	/* returns a, i.e., Dirac delta function */
	double aa = fabs(a);
	if (a!=0 && (aa<1e-30 || aa>1e30))
		output_warning("random_degenerate(a=%g): a is outside normal bounds of +/-1e(+/-30)", a);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	return a;
}

/** Generate a uniformly distributed random number 

	The probability density function for the uniform distribution is
	\f[ \varphi\left(x\right) = \left\{
		\begin{array}{c c}
			\frac{1}{b-a} & a \leq x < b \\
			0 & x<a ; x\geq b
		\end{array}
		\right\}
	\f]

	Note that this uniform distribution includes \e a but does not include \e b.
 **/
double random_uniform(unsigned int *state, /**< the rng state */
					  double a, /**< the minimum number */ 
					  double b) /**< the maximum number */
{
	/* uniform distribution in range (a,b( */
	double aa=fabs(a), ab=fabs(b);
	if (a!=0 && (aa<1e-30 || aa>1e30))
		output_warning("random_uniform(a=%g, b=%g): a is outside normal bounds of +/-1e(+/-30)", a, b);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	if (b!=0 && (ab<1e-30 || ab>1e30))
		output_warning("random_uniform(a=%g, b=%g): b is outside normal bounds of +/-1e(+/-30)", a, b);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	if (b<a)
		output_warning("random_uniform(a=%g, b=%g): b is less than a", a, b);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	return randunit(state)*(b-a)+a;
}

/** Generate a Gaussian distributed random number 

	The probability density function for the Gaussian (normal) distribution is
	\f[ \varphi\left(x\right) = \frac{1}{\sqrt{2\pi}\sigma}e^{\frac{\left(x-\mu\right)^2}{2\sigma^2}}	\f]
 
	Normally distributed random numbers are generated using the Box-Muller method:

	\code
	double random_normal(double m, double s)
	{
		double r, a, b;
		do { 
			a = 2*randunit(NULL)-1;
			b = 2*randunit(NULL)-1;
			r = a*a+b*b;
		} while (r>=1);
		return sqrt(-2*log(r)/r)*a*r*s+m;
	}
	\endcode
	
**/
double random_normal(unsigned int *state, /**< the rng state */
					 double m, /**< the mean of the distribution */ 
					 double s) /**< the standard deviation of the distribution */
{
	/* normal distribution centered on m, with variance s^2 */
	double r=randunit(state);
	if (s<0)
		output_warning("random_normal(m=%g, s=%g): s is negative", m, s);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	while (r<=0 || r>1)
		r=randunit(state);
	return sqrt(-2*log(r)) * sin(2*PI*randunit(state))*s+m;
}

/** Generate a Bernoulli distributed random number 

	The probability density function for the Bernoulli distribution is
	\f[ Prob\left\{x=1\right\} = 1-Prob\left\{x=0\right\} = p \f]

	Note that the Bernoulli distribution is a discrete distribution.
 **/
double random_bernoulli(unsigned int *state, /**< the rng state */
					    double p) /**< the probability of generating a 1 */
{
	double ap = fabs(p);
	if (ap!=0 && (ap<1e-30 || ap>1e30))
		output_warning("random_bernoulli(p=%g): p is not within the normal bounds of +/-1e(+/-30)", p);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
if (p<0 || p>1)
		output_warning("random_bernoulli(p=%g): p is not between 0 and 1", p);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	/* 1 if rand<=p, 0 if rand>p */
	return (p>=randunit(state)) ? 1 : 0;
}

/** Generate a number randomly sample uniformly from a list 

	The probability that the value \e a is drawn from the sample is

	\f[ Prob\left\{x=a\right\} = \frac{1}{n} \f]

	Note that the sampled distriution is a discrete distribution.
 **/
double random_sampled(unsigned int *state, /**< the rng state */
					  unsigned n, /**< the number of samples in the list */
					  double *x) /**< the sample list */
{
	if (n>0)
	{
		double v = x[(unsigned)(randunit(state)*n)];
		double av = fabs(v);
		if (v!=0 && (av<1e-30 || av>1e30))
			output_warning("random_sampled(n=%d,...): sampled value is not within normal bounds of +/-1e(+/-30)",n);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
		return v;
	}
	else
	{
		throw_exception("random_sampled(n=%d,...): n must be a positive number", n);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
		return QNAN; /* never gets here */
	}
}


/** Generate a Pareto distributed random number 

 	The Pareto distribution is one in which the probability 
	of drawing a number less than \p x is proportional to
	x^k.  The probability density function of the Pareto distribution is
	\f[ \varphi\left( x<k \right) = k \frac{m^k}{x^{k+1}} x \geq m \f]
	The cumulative density function is \f[ \varphi\left( x<k \right) = 1-(\frac{m}{x})^k \f].
**/
double random_pareto(unsigned int *state, /**< the rng state */
					 double m, /**< the minimum value */
					 double k) /**< the k value */
{
	double am = fabs(m);
	double ak = fabs(k);
	double r = randunit(state);
	if (am!=0 && (am<1e-03 || am>1e30))
		output_warning("random_pareto(m=%g, k=%g): m is not within the normal bounds of +/-1e(+/-30)", m, k);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	if (ak>1e30)
		output_warning("random_pareto(m=%g, k=%g): k is not within the normal bounds of +/-1e(+/-30)", m, k);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	if (k<=0)
		throw_exception("random_pareto(m=%g, k=%g): k must be greater than 1", m, k);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	while (r<=0 || r>=1)
		r = randunit(state);
	return m*pow(r,-1/k);
}

/** Generate a log Gaussian distributed random number 

	The log-normal probability density function is
	\f[ \varphi\left(x\right) = \frac{1}{\sqrt{2\pi}x\sigma}e^{\frac{\left(\ln x-\mu\right)^2}{2\sigma^2}}	\f]
 **/
double random_lognormal(unsigned int *state, /**< the rng state */
					    double gmu, /**< the geometric mean */
						double gsigma) /**< the geometric standard deviation */
{
	return exp(random_normal(state,0,1)*gsigma+gmu);
}

/** Generate an exponentially distributed random number 

	The exponential probability density function is
	\f[ \varphi\left(x\right) = \left\{
		\begin{array}{c c}
			\lambda e^{-\lambda x} & x \geq o \\
			0 & x < 0 
		\end{array}
		\right\}
	\f]
 **/
double random_exponential(unsigned int *state, /**< the rng state */
					      double lambda) /**< the rate parameter lambda */
{
	double r=randunit(state);
	if (lambda<=0)
		throw_exception("random_exponential(l=%g): l must be greater than 0", lambda);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	if (lambda<1e-30 || lambda>1e30)
		output_warning("random_exponential(l=%g): l is not within the normal bounds of 1e(+/-30)", lambda);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	while (r<=0 || r>=1)
		r=randunit(state);
	return -log(r)/lambda;
}

/** Generate a Weibull distributed random number

	The Weibull probability density function is

	\f[ \varphi\left(x;k,\lambda\right) = \frac{k}{\lambda} \left( \frac{x}{\lambda} \right)^{k-1} e^{-\left(\frac{x}{\lambda}\right)^k} \f]

	@note This distribution is not tested because the test requires the Gamma function, which itself would have to be implemented and tested.

 **/
double random_weibull(unsigned int *state, /**< the rng state */
					  double lambda, /**< scale parameter */
					  double k) /**< rate shape parameter */
{
	if (k<=0)
		throw_exception("random_weibull(l=%g, k=%g): k must be greater than 0", lambda, k);
		/* TROUBLESHOOT
			An attempt to generate a random number used a parameter that was outside the expected range of real numbers.  
			Correct the functional definition of the random number and try again.
		 */
	return lambda * pow(-log(1-randunit(state)),1/k);	
}

/** Generate a Rayleigh distributed random number

	The Rayleigh probability density function is 

	\f[ \varphi \left( x;\sigma \right) = \frac{x e^{-\frac{x^2}{2\sigma^2}} }{\sigma^2} \f]

 **/
double random_rayleigh(unsigned int *state, /**< the rng state */
					   double sigma) /**< mode parameter */
{
	return sigma*sqrt(-2*log(1-randunit(state)));
}

/** Generate a Gamma distributed random number

	The Gamma probability density function is

	\f[ \varphi \left( x; \alpha,\beta\right) = \frac{1}{\Gamma(\alpha) \beta^\alpha} x^{\alpha-1} e^{-x/\beta} \f]

 **/
double random_gamma(unsigned int *state, /**< the rng state */
					double alpha, double beta)
{
	/* used a different method depending on alpha */
	double na = floor(alpha);
	if (fabs(na-alpha)<1e-8 && na<12) /* alpha is an integer andsafe against underflow */
	{
		unsigned int i;
		double prod = 1;
		for (i=0; i<na; i++)
			prod *= randunit_pos(state);
		return -beta * log(prod);
	}
	else if (na<1) /* a is small */
	{
		double p, q, x, u, v;
		p = E/(alpha+E);
		do {
			u = randunit(state);
			v = randunit_pos(state);
			if (u<p)
			{
				x = exp((1/alpha)*log(v));
				q = exp(-x);
			}
			else
			{
				x = 1 - log(v);
				q = exp((alpha-1)*log(x));
			}
		} while (randunit(state)>=q);
		return beta*x;
	}
	else /* a is large */
	{
		double sqrta = sqrt(2*alpha-1);
		double x, y, v;
		do {
			do {
				y = tan(PI*randunit(state));
				x = sqrta*y+alpha-1;
			} while (x<=0);
			v = randunit(state);
		} while (v>(1+y*y) * exp((alpha-1)*log(x/(alpha-1))-sqrta*y));
		return beta*x;
	}
}

/** Generate a Beta distributed random number

	The Beta probability density function is

	\f[ \varphi \left( x; \alpha,\beta\right) = \frac{\Gamma(\alpha+\beta)}{\Gamma(\alpha) \Gamma(\beta)} x^(\alpha-1) (1-x)^{\beta-1} \f]

 **/

double random_beta(unsigned int *state, /**< the rng state */
				   double alpha, double beta) /**< event parameters */
{
	/* use the transformer generator */
	double x1 = random_gamma(state,alpha,1);
	double x2 = random_gamma(state,beta,1);
	return x1 / (x1+x2);
}

/** Generate a symmetric triangle distributed random number

    The triangle probability density function is

	\f[ \varphi\left(x|a,b\right) = \left\{
		\begin{array}{c c}
			\frac{4(x-a)}{(b-a)^2} & a < x \leq (a+b)/2 \\
			\frac{4(b-x)}{(b-a)^2} & (a+b)/2 < x \leq b \\
			0 & x \leq a | x > b
		\end{array}
		\right\}
	\f]

 **/

double random_triangle(unsigned int *state, /**< the rng state */
					   double a, double b)
{
	return (randunit(state) + randunit(state))*(b-a)/2 + a;
}

/* internal function that generates a random number */
double _random_value(RANDOMTYPE type, unsigned int *state, va_list ptr)
{
	switch (type) {
	case RT_DEGENERATE:/* ... double value */
		{	double a = va_arg(ptr,double);
			return random_degenerate(state, a);
		}
	case RT_UNIFORM:		/* ... double min, double max */
		{	double min = va_arg(ptr,double);
			double max = va_arg(ptr,double);
			return random_uniform(state,min,max);
		}
	case RT_NORMAL:		/* ... double mean, double stdev */
		{	double mu = va_arg(ptr,double);
			double sigma = va_arg(ptr,double);
			return random_normal(state,mu,sigma);
		}
	case RT_BERNOULLI:	/* ... double p */
		return random_bernoulli(state,va_arg(ptr,double));
	case RT_SAMPLED: /* ... unsigned n_samples, double samples[n_samples] */
		{	unsigned n_samples = va_arg(ptr,unsigned);
			double *samples = va_arg(ptr,double*);
			return random_sampled(state,n_samples,samples);
		}
	case RT_PARETO:	/* ... double base, double gamma */
		{	double base = va_arg(ptr,double);
			double gamma = va_arg(ptr,double);
			return random_pareto(state,base,gamma);
		}
	case RT_LOGNORMAL:	/* ... double gmean, double gsigma */
		{	double gmu = va_arg(ptr,double);
			double gsigma = va_arg(ptr,double);
			return random_lognormal(state,gmu,gsigma);
		}
	case RT_EXPONENTIAL: /* ... double lambda */
		{	double lambda = va_arg(ptr,double);
			return random_exponential(state,lambda);
		}
	case RT_RAYLEIGH: /* ... double sigma */
		{	double sigma = va_arg(ptr,double);
			return random_rayleigh(state,sigma);
		}
	case RT_WEIBULL: /* ... double lambda, double k */
		{	double lambda = va_arg(ptr,double);
			double k = va_arg(ptr,double);
			return random_weibull(state,lambda,k);
		}
	case RT_GAMMA: /* ... double alpha, double beta */
		{	double alpha = va_arg(ptr,double);
			double beta = va_arg(ptr,double);
			return random_gamma(state,alpha,beta);
		}
	case RT_BETA: /* ... double alpha, double beta */
		{	double alpha = va_arg(ptr,double);
			double beta = va_arg(ptr,double);
			return random_beta(state,alpha,beta);
		}
	case RT_TRIANGLE: /* ... double a, double b */
		{	double a = va_arg(ptr,double);
			double b = va_arg(ptr,double);
			return random_triangle(state,a,b);
		}
	default:
		throw_exception("_random_value(type=%d,...); type is not valid",type);
		/* TROUBLESHOOT
			An attempt to generate a random number specific a distribution type that isn't recognized.
			Check that the distribution is valid and try again.
		 */
	}
	return QNAN; /* never gets here */
}

/** Convert a random distribution to a string spec
 **/
int _random_specs(RANDOMTYPE type, double a, double b,char *buffer,int size)
{
	switch ( type ) {
	case RT_DEGENERATE:/* ... double value */
		return snprintf(buffer,size-1,"degenerate(%lg)",a);
	case RT_UNIFORM:		/* ... double min, double max */
		return snprintf(buffer,size-1,"uniform(%lg,%lg)",a,b);
	case RT_NORMAL:		/* ... double mean, double stdev */
		return snprintf(buffer,size-1,"normal(%lg,%lg)",a,b);
	case RT_BERNOULLI:	/* ... double p */
		return snprintf(buffer,size-1,"bernoulli(%lg,%lg)",a,b);
	case RT_SAMPLED: /* ... unsigned n_samples, double samples[n_samples] */
		return snprintf(buffer,size-1,"sampled(%lg,%lg)",a,b);
	case RT_PARETO:	/* ... double base, double gamma */
		return snprintf(buffer,size-1,"pareto(%lg,%lg)",a,b);
	case RT_LOGNORMAL:	/* ... double gmean, double gsigma */
		return snprintf(buffer,size-1,"lognormal(%lg,%lg)",a,b);
	case RT_EXPONENTIAL: /* ... double lambda */
		return snprintf(buffer,size-1,"exponential(%lg,%lg)",a,b);
	case RT_RAYLEIGH: /* ... double sigma */
		return snprintf(buffer,size-1,"rayleigh(%lg,%lg)",a,b);
	case RT_WEIBULL: /* ... double lambda, double k */
		return snprintf(buffer,size-1,"weibull(%lg,%lg)",a,b);
	case RT_GAMMA: /* ... double alpha, double beta */
		return snprintf(buffer,size-1,"gamma(%lg,%lg)",a,b);
	case RT_BETA: /* ... double alpha, double beta */
		return snprintf(buffer,size-1,"beta(%lg,%lg)",a,b);
	case RT_TRIANGLE: /* ... double a, double b */
		return snprintf(buffer,size-1,"triangle(%lg,%lg)",a,b);
	default:
		throw_exception("_random_specs(type=%d,...); type is not valid",type);
		/* TROUBLESHOOT
			An attempt to describe a random number specific a distribution type that isn't recognized.
			Check that the distribution is valid and try again.
		 */
	}
	return -1; /* never gets here */
}

/** Apply a random number to property of a group of objects
	@return the number of objects changed
 **/
int random_apply(const char *group_expression, /**< the group definition; see find_objects() */
				 const char *property, /**< the property to update */
				 int type, /**< the distribution type */
				 ...) /**< the distribution's parameters */
{
	FINDLIST *list = find_objects(FL_GROUP, group_expression);
	OBJECT *obj;
	unsigned count=0;
	va_list ptr;
	va_start(ptr,type);
	for ( obj = find_first(list) ; obj != NULL ; obj = find_next(list,obj) )
	{
		/* this is quite slow and should use a class property lookup */
		object_set_double_by_name(obj,property,_random_value((RANDOMTYPE)type,NULL,ptr));
		count++;
	}
	va_end(ptr);
	return count;
}

/** Generate a random value
	@return a double containing the random number
 **/
double random_value(int type, /**< the type of distribution desired */
					...) /**< the distribution's parameters */
{
	double x;
	va_list ptr;
	va_start(ptr,type);
	x = _random_value((RANDOMTYPE)type,NULL,ptr);
	va_end(ptr);
	return x;
}

/** Generate a pseudo-random value using the known state that is updated.
	@return a double containing the random number
 **/
double pseudorandom_value(RANDOMTYPE type, /**< the type of distribution desired */
						  unsigned int *state, /**< the state of the random number generator */
						  ...)/**< the distribution's parameters */
{
	double x;
	va_list ptr;
	va_start(ptr,state);
	x = _random_value(type,state,ptr);
	va_end(ptr);
	return x;
}

/******************************************************************************/
static double mean(double sample[], unsigned int count)
{
	double sum=0;
	unsigned int i;
	for (i=0; i<count; i++)
		sum += sample[i];
	return sum/count;
}
#ifdef min
#undef min
#endif
static double min(double sample[], unsigned int count)
{
	double min;
	unsigned int i;
	for (i=0; i<count; i++)
	{
		if (i==0) min=sample[0];
		else if (sample[i]<min) min=sample[i];
	}
	return min;
}
#ifdef max
#undef max
#endif
static double max(double sample[], unsigned int count)
{
	double max;
	unsigned int i;
	for (i=0; i<count; i++)
	{
		if (i==0) max=sample[0];
		else if (sample[i]>max) max=sample[i];
	}
	return max;
}
static double stdev(double sample[], unsigned int count)
{
	double sum=0, mean=0;
	unsigned int n = 0, i;
	for (i=0; i<count; i++)
	{
		double delta = sample[i] - mean;
		n++;
		mean += delta/n;
		sum += delta*(sample[i]-mean);
	}
	return sqrt(sum/(n-1));
}
static int report(const char *parameter, double actual, double expected, double error)
{
	if (parameter==NULL)
	{
		output_test("   Parameter       Actual    Expected    Error");
		output_test("---------------- ---------- ---------- ----------");
		return 0;
	}
	else
	{
		int iserror = fabs(actual-expected)>error ? 1 : 0;
		if (expected==0)
			output_test("%-16.16s %10.4f %10.4f %9.6f  %s", parameter,actual,expected,actual-expected, iserror?"ERROR":"");
		else
			output_test("%-16.16s %10.4f %10.4f %9.6f%% %s", parameter,actual,expected,(actual-expected)/expected*100, iserror?"ERROR":"");
		return iserror;
	}
}

/** Test random distributions

	To run the self-test, use the \p --randtest command-line argument.  
	The test results are output to the file specified by the \p global_testoutputfile variable.
	@return number of failed tests
 **/
int random_test(void)
{
	int failed = 0, ok=0, errorcount=0, preverrors=0;
	static double sample[1000000];
	double a, b;
	unsigned int count = sizeof(sample)/sizeof(sample[0]);
	unsigned int i;
	unsigned int initstate, state;

	output_test("\nBEGIN: random random distributions tests");

	/* Dirac distribution test */
	a = 10*randunit(NULL)/2-5;
	output_test("\ndegenerate(x=%g)",a);
	for (i=0; i<count; i++)
	{
		sample[i] = random_degenerate(NULL,a);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0);
	errorcount+=report("Mean",mean(sample,count),a,0.01);
	errorcount+=report("Stdev",stdev(sample,count),0,0.01);
	errorcount+=report("Min",min(sample,count),a,0.01);
	errorcount+=report("Max",max(sample,count),a,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* uniform distribution test */
	a = 10*randunit(NULL)/2;
	b = 10*randunit(NULL)/2 + 5;
	output_test("\nuniform(min=%g, max=%g)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_uniform(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0);
	errorcount+=report("Mean",mean(sample,count),(a+b)/2,0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt((b-a)*(b-a)/12),0.01);
	errorcount+=report("Min",min(sample,count),a,0.01);
	errorcount+=report("Max",max(sample,count),b,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* Bernoulli distribution test */
	a = randunit(NULL);
	output_test("\nBernoulli(prob=%g)",a);
	for (i=0; i<count; i++)
	{
		sample[i] = random_bernoulli(NULL,a);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),a,0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt(a*(1-a)),0.01);
	errorcount+=report("Min",min(sample,count),0,0.01);
	errorcount+=report("Max",max(sample,count),1,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* normal distribution test */
	a = 20*randunit(NULL)-5;
	b = 5*randunit(NULL);
	output_test("\nnormal(mean=%g, stdev=%g)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_normal(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),a,0.01);
	errorcount+=report("Stdev",stdev(sample,count),b,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* exponential distribution test */
	a = 1/randunit(NULL)-1;
	output_test("\nexponential(lambda=%g)",a);
	for (i=0; i<count; i++)
	{
		sample[i] = random_exponential(NULL,a);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),1/a,0.01);
	errorcount+=report("Stdev",stdev(sample,count),1/a,0.01);
	errorcount+=report("Min",min(sample,count),0,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;
	
	/* lognormal distribution test */
	a = 2*randunit(NULL)-1;
	b = 2*randunit(NULL);
	output_test("\nlognormal(gmean=%g, gstdev=%g)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_lognormal(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),exp(a+b*b/2),0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt((exp(b*b)-1)*exp(2*a+b*b)),0.1);
	errorcount+=report("Min",min(sample,count),0,0.1);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* Pareto distribution test */
	a = 10*randunit(NULL);
	b = randunit(NULL)+2.5;
	output_test("\nPareto(base=%g, gamma=%g)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_pareto(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),b*a/(b-1),0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt(a*a*b/((b-1)*(b-1)*(b-2))),0.25);
	errorcount+=report("Min",min(sample,count),a,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* rayleigh distribution test */
	a = 10*randunit(NULL);
	b = 4*randunit(NULL);
	output_test("\nRayleigh(sigma=%g)",a);
	for (i=0; i<count; i++)
	{
		sample[i] = random_rayleigh(NULL,a);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),a*sqrt(3.1415926/2),0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt((4-3.1415926)/2*a*a),0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* beta distribution test */
	a = 15*randunit(NULL);
	b = 4*randunit(NULL);
	output_test("\nBeta(a=%f,b=%f)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_beta(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),a/(a+b),0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt(a*b/((a+b)*(a+b)*(a+b+1))),0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* gamma distribution test */
	a = 15*randunit(NULL);
	b = 4*randunit(NULL);
	output_test("\nGamma(a=%f,b=%f)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_gamma(NULL,a,b);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),a*b,0.25);
	errorcount+=report("Stdev",stdev(sample,count),sqrt(a*b*b),0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* triangle distribution test */
	a = -randunit(NULL)*10;
	b = randunit(NULL)*10;
	output_test("\nTriangle(a=%f,b=%f)",a,b);
	for (i=0; i<count; i++)
	{
		sample[i] = random_triangle(NULL,a,b);
		if (!isfinite(sample[i]))
			output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),(a+b)/2,0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt((a-b)*(a-b)/24),0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* sampled distribution test */
	output_test("\nSampled(count=10, sample=[0..9])");
	for (i=0; i<count; i++)
	{
		double set[10]={0,1,2,3,4,5,6,7,8,9};
		sample[i] = random_sampled(NULL,10,set);
		if (!isfinite(sample[i]))
			failed++,output_test("Sample %d is not a finite number!",i--);
	}
	errorcount+=report(NULL,0,0,0.01);
	errorcount+=report("Mean",mean(sample,count),4.5,0.01);
	//report("Stdev",stdev(sample,count),sqrt(9*9/12),0.01);
	errorcount+=report("Stdev",stdev(sample,count),sqrt(99/12),0.1); /* sqrt((b-a+1)^2-1 / 12)*/ /* 2.87 is more accurate and was Mathematica's answer */
	errorcount+=report("Min",min(sample,count),0,0.01);
	errorcount+=report("Max",max(sample,count),9,0.01);
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* test non-deterministic sequences */
	output_test("\nNon-deterministic test (N=%d)",count);
	for (i=0; i<count; i++)
		sample[i] = random_value(RT_NORMAL,0.0,1.0);
	for (i=0; i<count; i++)
	{
		double v = random_value(RT_NORMAL,0.0,1.0);
		if ( sample[i] == v )
			failed++,output_test("Sample %d matched (%f==%f)", i, sample[i],v);
	}	
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* test deterministic sequences */
	initstate = state = rand();
	output_test("\nDeterministic test for state %u (N=%d)",initstate,count);
	for (i=0; i<count; i++)
		sample[i] = pseudorandom_value(RT_UNIFORM,&state,0.0,1.0);
	state = initstate;
	for (i=0; i<count; i++)
	{
		double v = pseudorandom_value(RT_UNIFORM,&state,0.0,1.0);
		if (sample[i] != v)
			failed++,output_test("Sample %d did not match (%f!=%f)", i, sample[i],v);
	}	
	if (preverrors==errorcount)	ok++; else failed++;
	preverrors=errorcount;

	/* test modulus */
	initstate = state;
	output_test("\nTesting modulus starting at state 0x%08x", state);
	for ( randwarn(&state),count=1; state!=initstate && count!=0 ; count++)
		randwarn(&state);
	if ( count==0 )
		output_test("Modulus exceeds 2^32");
	else
		output_test("Modulus = %d", count);

	/* report results */
	if (failed)
	{
		output_error("randtest: %d random distributions tests failed--see test.txt for more information",failed);
		output_test("!!! %d random distributions tests failed, %d errors found",failed,errorcount);
	}
	else
	{
		IN_MYCONTEXT output_verbose("%d random distributions tests completed with no errors--see test.txt for details",ok);
		output_test("randtest: %d random distributions tests completed, %d errors found",ok,errorcount);
	}
	output_test("END: random distributions tests");
	return failed;
}

//////////////////////////////////////////////////////////////////////////////////////////////////
// Random Variables

static randomvar *randomvar_list = NULL;
static unsigned int n_randomvars = 0;
clock_t randomvar_synctime = 0;

int convert_to_randomvar(const char *string, void *data, PROPERTY *prop)
{
	//output_verbose("convert_to_randomvar(string='%-.64s...', ...)",string);
	randomvar *var = (randomvar*)data;
	char buffer[1024];
	char *token = NULL;
	char *last = NULL;

	/* clean memory */
	randomvar *next = var->next;
	memset(var,0,sizeof(randomvar));
	var->next = next;

	/* check string length before copying to buffer */
	if ( strlen(string) > sizeof(buffer)-1 )
	{
		output_error("convert_to_randomvar(string='%-.64s...', ...) input string is too long (max is 1023)",string);
		return 0;
	}
	strcpy(buffer,string);

	/* parse tuples separate by semicolon*/
	while ( (token=strtok_s(token==NULL?buffer:NULL,";",&last)) != NULL)
	{
		/* colon separate tuple parts */
		char *param = token;
		char *value = strchr(token,':');

		/* isolate param and token and eliminate leading whitespaces */
		while ( *param != '\0' && (isspace(*param)||iscntrl(*param)) ) 
		{
			param++;		
		}
		if ( value == NULL )
		{
			char *one = NULL;
			if ( ! one )
			{
				one = strdup("1");
			}
			value = one;
		}
		else
		{
			*value++ = '\0'; /* separate value from param */
		}
		while ( isspace(*value) || iscntrl(*value) )
		{
			value++;
		}

		// parse params
		//output_verbose("convert_to_randomvar(string='%-.64s...', ...) processing param '%s' value '%s'",string,param,value);
		if ( strcmp(param,"type") == 0 )
		{
			char *a;
			a = strchr(value,'(');
			if ( a )
			{
				int nargs;
				*a++ = '\0';
				var->type = random_type(value);
				if ( var->type == RT_INVALID )
				{
					output_error("convert_to_randomvar(string='%-.64s...', ...) type '%s' is invalid",string,value);
					return 0;
				}
				var->a = atof(a);
				nargs = random_nargs(value);
				if ( nargs == 2 )
				{
					char *b = strchr(a,',');
					if ( b )
					{
						*b++ = '\0';
						var->b = atof(b);
					}
					else
					{
						output_error("convert_to_randomvar(string='%-.64s...', ...) missing second arg in type spec '%s'",string,value);
						return 0;
					}
				}
			}
			else
			{
				output_error("convert_to_randomvar(string='%-.64s...', ...) missing '(' in type spec '%s'",string,value);
				return 0;
			}
		}
		else if (strcmp(param,"min")==0)
		{
			var->low = atof(value);
		}
		else if (strcmp(param,"max")==0)
		{
			var->high = atof(value);
		}
		else if (strcmp(param,"refresh")==0)
		{
			char unit[256];
			if ( sscanf(value,"%d%s",&(var->update_rate),unit) == 2 )
			{
				double dt = var->update_rate;
				if ( !unit_convert(unit,"s",&dt) )
				{
					output_error("convert_to_randomvar(string='%-.64s...', ...) refresh unit '%s' is not valid",string,unit);
					return 0;
				}
				else
				{
					var->update_rate = (int)dt;
				}
			}
		}
		else if ( strcmp(param,"state") == 0 )
		{
			var->state = atoi(value);
		}
		else if (strcmp(param,"integrate") == 0 )
		{
			var->flags |= RNF_INTEGRATE;
		}
		else if ( strcmp(param,"correlation") == 0 )
		{
			char source_name[129];
			char object_name[64];
			char property_name[64];
			double scale=1.0, bias=0.0;
			if ( sscanf(value,"%[^*]*%lg%lg",source_name,&scale,&bias) < 1 )
			{
				output_error("convert_to_randomvar(string='%-.64s...',...) correlation specification is invalid",string);
				return 0;
			}
			var->correlation = (CORRELATION*)malloc(sizeof(CORRELATION));
			if ( var->correlation == NULL )
			{
				output_error("convert_to_randomvar(string='%-.64s...',...) memory allocation failed",string);
				return 0;				
			}
			if ( sscanf(source_name,"%[^.].%[^\n]",object_name,property_name) != 2 )
			{
				var->correlation->object = load_get_current_object();
				if ( var->correlation->object )
				{
					strcpy(property_name,source_name);
				}
				else
				{
					output_error("convert_to_randomvar(string='%-.64s...',...) missing object name",string);
					return 0;				
				}
			} 
			else
			{
				var->correlation->object = object_find_name(object_name);
			}
			if ( var->correlation->object == NULL )
			{
				output_error("convert_to_randomvar(string='%-.64s...',...) object '%s' not found", string, object_name);
				return 0;
			}
			var->correlation->property = class_find_property(var->correlation->object->oclass,property_name);
			if ( var->correlation->property == NULL )
			{
				output_error("convert_to_randomvar(string='%-.64s...',...) property '%s' not found", string, property_name);
				return 0;
			}
			var->correlation->source = object_get_double(var->correlation->object,var->correlation->property);
			if ( var->correlation->source == NULL )
			{
				output_error("convert_to_randomvar(string='%-.64s...',...) source '%s.%s' is not a double", string, object_name, property_name);
				return 0;
			}	
			var->correlation->scale = scale;
			var->correlation->bias = bias;		
		}
		/* fixed value */
		else if (param[0]=='-' || param[0]=='+' || isdigit(param[0]) || param[0]=='.')
		{
			var->type = RT_DEGENERATE;
			var->a = atof(param);
		}
		else if (strcmp(param,"")!=0)
		{
			output_error("convert_to_randomvar(string='%-.64s...', ...) parameter '%s' is not valid",string,param);
			return 0;
		}
	}

	/* reinitialize the randomvar */
	if (!randomvar_update(var))
		return 0;

	/* everything converted ok */
	return 1;
}

int convert_from_randomvar(char *string,int size,void *data, PROPERTY *prop)
{
	randomvar *var = (randomvar*)data;
	return snprintf(string,size-1,"%lf",var->value);
}

int initial_from_randomvar(char *string, int size, void *data, PROPERTY *prop)
{
	randomvar *var = (randomvar*)data;
	char buffer[2048];
	char tmp[1024];
	if ( _random_specs(var->type,var->a,var->b,tmp,sizeof(tmp)-1) )
	{
		int len = snprintf(buffer,sizeof(buffer)-1,"type:%s",tmp);
		if ( var->low != 0.0 && var->low < var->high )
		{
			len += snprintf(buffer+len,sizeof(buffer)-1-len,"; min:%g",var->low);
		}
		if ( var->high != 0.0 && var->low < var->high )
		{
			len += snprintf(buffer+len,sizeof(buffer)-1-len,"; max:%g",var->high);
		}
		if ( var->update_rate != 0 )
		{
			len += snprintf(buffer+len,sizeof(buffer)-1-len,"; refresh:%d",var->update_rate);
		}
		if ( (var->flags&RNF_INTEGRATE) == RNF_INTEGRATE )
		{
			len += snprintf(buffer+len,sizeof(buffer)-1-len,"; integrate");
		}
		if ( var->correlation != NULL )
		{
			object_name(var->correlation->object,tmp,sizeof(tmp)-1);
			len += snprintf(buffer,sizeof(buffer)-1-len,"; correlate:%s.%s*%lg%+lg",
				tmp, var->correlation->property->name, var->correlation->scale, var->correlation->bias);
		}
		len += snprintf(buffer+len,sizeof(buffer)-1-len,"; state:%u",var->state);
		if ( string )
		{
			if ( snprintf(string,size,"%.*s",len,buffer) < len )
			{
				output_warning("convert_from_randomvar(...): long output truncated to fit in return buffer");
			}
		}
		return len;
	}
	else
	{
		output_error("initial value of randomvar type %d cannot be reconstructred",var->type);
		return -1;
	}
}

int randomvar_create(void *ptr)
{
	static randomvar *last = NULL;
	randomvar *var = (randomvar*)ptr;
	memset(var,0,sizeof(randomvar));
	var->state = randwarn(NULL);
	var->next = NULL;
	if ( randomvar_list == NULL )
	{
		randomvar_list = var;
	}
	if ( last )
	{
		last->next = var;
	}
	last = var;
	n_randomvars++;
	return 1;
}

int randomvar_update(randomvar *var)
{
	do {
		double v = pseudorandom_value(var->type,&(var->state),var->a,var->b);
		if ( var->correlation )
		{
			double vv = v + (*(var->correlation->source)) * var->correlation->scale + var->correlation->bias;
			IN_MYCONTEXT output_debug("randomvar_update(): correlation is to %s.%s: %g + %g*%g%+g -> %g", var->correlation->object->name, var->correlation->property->name, v, *(var->correlation->source), var->correlation->scale, var->correlation->bias, vv);
			v = vv;
		}
		if ( var->flags&RNF_INTEGRATE )
		{
			var->value += v;
		}
		else
		{
			var->value = v;
		}
	} while ( var->low<var->high && !( var->low<var->value && var->value<var->high ) );
	return 1;
}

int randomvar_init(randomvar *var)
{
	randomvar_update(var);
	return 1;
}

int randomvar_initall(void)
{
	randomvar *var;
	for (var=randomvar_list; var!=NULL; var=var->next)
	{
		if (randomvar_init(var)==1)
			return FAILED;
	}
	return SUCCESS;
}

TIMESTAMP randomvar_sync(randomvar *var, TIMESTAMP t1)
{
	if ( var->update_rate<=0 || t1%var->update_rate==0 )
		randomvar_update(var);
	return var->update_rate<=0 ? TS_NEVER : ((t1/var->update_rate)+1)*var->update_rate;
}

randomvar *randomvar_getnext(randomvar*var)
{
	return var ? var->next : randomvar_list;
}

size_t randomvar_getspec(char *str, size_t size, const randomvar *var)
{
	char buffer[2048];
	char specs[1024];
	size_t len;
	if ( _random_specs(var->type,var->a,var->b,specs,sizeof(specs))<=0 )
		return 0;
	snprintf(buffer,sizeof(buffer)-1,"state: %u; type: %s; min: %g; max: %g; refresh: %u%s",
		var->state, specs, var->low, var->high, var->update_rate, var->flags&RNF_INTEGRATE ? "; integrate" : "");
	len = strlen(buffer);
	if ( len > 0 && snprintf(str,size,"%.*s",(int)(len),buffer) < (int)len )
	{
		output_warning("randomvar_getspec(...): long output truncated to fit in return buffer");
		return size-1;
	}
	else
	{
		return len;
	}
}

TIMESTAMP randomvar_syncall(TIMESTAMP t1)
{
	if ( randomvar_list )
	{
		randomvar *var = NULL;
		TIMESTAMP t2 = TS_NEVER;
		clock_t ts = (clock_t)exec_clock();
		while ( (var=randomvar_getnext(var)) != NULL )
		{
			TIMESTAMP t3 = randomvar_sync(var,t1);
			if ( absolute_timestamp(t3)<absolute_timestamp(t2) ) t2 = t3;
		}
		randomvar_synctime += (clock_t)exec_clock() - ts;
		return t2!=TS_NEVER ? -absolute_timestamp(t2) : TS_NEVER;
	}
	else
		return TS_NEVER;
}

double random_get_part(void *x, const char *name)
{
	randomvar *v = (randomvar*)x;
	if ( strcmp(name,"a")==0 ) return v->a;
	if ( strcmp(name,"b")==0 ) return v->b;
	if ( strcmp(name,"high")==0 ) return v->high;
	if ( strcmp(name,"low")==0 ) return v->low;
	return QNAN;
}

int random_set_part(void *x, const char *name, const char *value)
{
	randomvar *v = (randomvar*)x;
#define SCAN(N,X,F) if ( strcmp(name,N) == 0 || strcmp(name,#X)==0 ) { return sscanf(value,F,&(v->X)); }
	SCAN("value",value,"%lg");
	SCAN("a",a,"%lg");
	SCAN("b",b,"%lg");
	SCAN("min",low,"%lg");
	SCAN("max",high,"%lg");
	SCAN("state",state,"%u");
	SCAN("refresh",update_rate,"%u");
	SCAN("flags",flags,"%u");
	if ( strcmp(name,"type") == 0 )
	{
		RANDOMTYPE type = random_type(value);
		if ( type == RT_INVALID )
		{
			char str[1024];
			double a,b;
			if ( sscanf(value,"%1023[^(](%lg,%lg)",str,&a,&b) == 3 && (type=random_type(str)) != RT_INVALID )
			{
				v->type = type;
				v->a = a;
				v->b = b;
				return 1;
			}
			else
			{
				IN_MYCONTEXT output_debug("random_set_part(void *x=%p, char *name='%s', char *value='%s'): type is not valid",x,name,value);
				return 0;
			}
		}
		else
		{
			v->type = type;
			return 1;
		}
	}
	else
	{
		IN_MYCONTEXT output_debug("random_set_part(void *x=%p, char *name='%s', char *value='%s'): name is not valid",x,name,value);
		return 0;
	}
}


/** @} **/

