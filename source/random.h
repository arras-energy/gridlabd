/* File: random.h 
 * Copyright (C) 2008, Battelle Memorial Institute

 	Copyright (C) 2008 Battelle Memorial Institute
	@file random.h
	@addtogroup random
	@ingroup core
 @{
 **/

#ifndef _RANDOM_H
#define _RANDOM_H

#if ! defined _GLDCORE_H && ! defined _GRIDLABD_H
#error "this header may only be included from gldcore.h or gridlabd.h"
#endif

#include "platform.h"
#include "timestamp.h"
#include "property.h"

typedef enum {
	RT_INVALID=-1,    /**< used to flag bad random types */
	RT_DEGENERATE=0,  /**< degenerate distribution (Dirac delta function); double only_value */
	RT_UNIFORM=1,     /**< uniform distribution; double minimum_value, double maximum_value */
	RT_NORMAL=2,      /**< normal distribution; double arithmetic_mean, double arithmetic_stdev */
	RT_LOGNORMAL=3,   /**< log-normal distribution; double geometric_mean, double geometric_stdev */
	RT_BERNOULLI=4,   /**< Bernoulli distribution; double probability_of_observing_1 */
	RT_PARETO=5,      /**< Pareto distribution; double minimum_value, double gamma_scale */
	RT_EXPONENTIAL=6, /**< exponential distribution; double coefficient, double k_scale */
	RT_SAMPLED=7,     /**< sampled distribution; unsigned number_of_samples, double samples[n_samples] */
	RT_RAYLEIGH=8,    /**< Rayleigh distribution; double sigma */
	RT_WEIBULL=9,     /**< Weibull distribution; double lambda, double k */
	RT_GAMMA=10,      /**< Gamma distribution; double alpha, double beta */
	RT_BETA=11,       /**< Beta distribution; double alpha, double beta */
	RT_TRIANGLE=12,   /**< Triangle distribution; double a, double b */
} RANDOMTYPE;

typedef struct s_correlation CORRELATION;
struct s_correlation {
	struct s_object_list *object;
	PROPERTY *property;
	double *source;
	double scale;
	double bias;
	struct s_correlation *next;
};

#ifdef __cplusplus
extern "C" {
#endif
	void random_init(const char *name,const char *value);
	int random_test(void);
	int randwarn(unsigned int *state);
	void random_key(unsigned long long *ptr, size_t len);
	double randunit(unsigned int *state);
	double random_degenerate(unsigned int *state, double a);
	double random_uniform(unsigned int *state, double a, double b);
	double random_normal(unsigned int *state, double m, double s);
	double random_bernoulli(unsigned int *state, double p);
	double random_sampled(unsigned int *state, unsigned int n, double *x);
	double random_pareto(unsigned int *state, double base, double gamma);
	double random_lognormal(unsigned int *state, double gmu, double gsigma);
	double random_exponential(unsigned int *state, double lambda);
	double random_functional(const char *text);
	double random_beta(unsigned int *state, double alpha, double beta);
	double random_gamma(unsigned int *state, double alpha, double beta);
	double random_weibull(unsigned int *state, double l, double k);
	double random_rayleigh(unsigned int *state, double s);
	double random_triangle(unsigned int *state, double a, double b);
	double random_triangle_asy(unsigned int *state, double a, double b, double c);
	int random_apply(const char *group_expression, const char *property, int type, ...);
	RANDOMTYPE random_type(const char *name);
	int random_nargs(const char *name);
	double random_value(int type, ...);
	bool random_from_string(const char *str, double *value);
	double pseudorandom_value(RANDOMTYPE, unsigned int *state, ...);
#ifdef __cplusplus
}
#endif

#define RNF_INTEGRATE 0x0001 /**< RNG flag for integral number, e.g., random walk */

typedef struct s_randomvar randomvar;
struct s_randomvar {
	double value;				/**< current value */
	unsigned int state;			/**< RNG state */
	RANDOMTYPE type;			/**< RNG distribution */
	double a, b;				/**< RNG distribution parameters */
	double low, high;			/**< RNG truncations limits */
	unsigned int update_rate;	/**< RNG refresh rate in seconds */
	unsigned int flags;			/**< RNG flags */
	CORRELATION *correlation;	// correlation 
	/* internal parameters */
	randomvar *next;
};

#ifdef __cplusplus
extern "C" {
#endif

int randomvar_update(randomvar *var);
int randomvar_create(void *ptr);
int randomvar_init(randomvar *var);
int randomvar_initall(void);
TIMESTAMP randomvar_sync(randomvar *var, TIMESTAMP t1);
TIMESTAMP randomvar_syncall(TIMESTAMP t1);
int convert_to_randomvar(const char *string, void *data, PROPERTY *prop);
int convert_from_randomvar(char *string,int size,void *data, PROPERTY *prop);
int initial_from_randomvar(char *string,int size,void *data, PROPERTY *prop);
unsigned int64 random_id(void);
double random_get_part(void *x, const char *name);
int random_set_part(void *x, const char *name, const char *value);
unsigned entropy_source(void);
randomvar *randomvar_getnext(randomvar *var);
size_t randomvar_getspec(char *str, size_t size, const randomvar *var);

#ifdef __cplusplus
}
#endif

#endif

/** @} **/
