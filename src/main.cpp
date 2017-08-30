#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_FLOPS 10000

double do_flops(int num)
{
    double a = 0.;
    for(int i =0; i < num; i++)
        a += 3.14;
    return a;
}


int main(int argc, char const *argv[]) {
    
    /* Initialize the PAPI library */
    int retval = PAPI_library_init(PAPI_VER_CURRENT);
    int EventSet = PAPI_NULL;
    long_long values[1];

    if (retval != PAPI_VER_CURRENT && retval > 0) {
        fprintf(stderr, "PAPI library version mismatch!\n");
        exit(1);
    }

    if (retval < 0) {
        fprintf(stderr, "Initialization error!\n");
        exit(1);
    }

    fprintf(stdout, "PAPI Version Number\n");
    fprintf(stdout, "MAJOR:    % d\n", PAPI_VERSION_MAJOR(retval));
    fprintf(stdout, "MINOR:    % d\n", PAPI_VERSION_MINOR(retval));
    fprintf(stdout, "REVISION: % d\n", PAPI_VERSION_REVISION(retval));
    
    /* Create the Event Set */
    if (PAPI_create_eventset(&EventSet) != PAPI_OK){
        fprintf(stderr, "PAPI create EventSet!\n");
        exit(1);
    }
    
    int native = 0x0;
    PAPI_event_info_t info;

    //native = 0x4000028;
    PAPI_event_name_to_code("perf::CACHE-REFERENCES", &native);
    printf("Event code: %d\n", native);
    if(PAPI_get_event_info(native, &info) != PAPI_OK){
        if (PAPI_enum_event(&native, 0) != PAPI_OK)
            fprintf(stderr, "PAPI native event!\n");
    }

    /* Add Total Instructions Executed to our Event Set */
    if ((retval = PAPI_add_named_event(EventSet, "PAPI_TOT_INS")) != PAPI_OK){
        fprintf(stderr, "PAPI add_event %d!\n", retval);
        exit(1);
     }
    /* Start counting events in the Event Set */
    if (PAPI_start(EventSet) != PAPI_OK){
        fprintf(stderr, "PAPI start()!\n");
        exit(1);
    }
    printf("something\n");

     /* Defined in tests/do_loops.c in the PAPI source distribution */
    do_flops(NUM_FLOPS);

    /* Read the counting events in the Event Set */
    if (PAPI_read(EventSet, values) != PAPI_OK){
        fprintf(stderr, "PAPI Read!\n");
        exit(1);
    }

    printf("After reading the counters: %lld\n",values[0]);

    /* Reset the counting events in the Event Set */
    if (PAPI_reset(EventSet) != PAPI_OK){
        fprintf(stderr, "PAPI reset!\n");
        exit(1);
    }

    do_flops(NUM_FLOPS);

    /* Add the counters in the Event Set */
    if (PAPI_accum(EventSet, values) != PAPI_OK){
        fprintf(stderr, "PAPI accum!\n");
        exit(1);
    }
    printf("After adding the counters: %lld\n",values[0]);

    do_flops(NUM_FLOPS);

    /* Stop the counting of events in the Event Set */
    if (PAPI_stop(EventSet, values) != PAPI_OK){
        fprintf(stderr, "PAPI stop!\n");
        exit(1);
    }
    
    printf("After stopping the counters: %lld\n",values[0]);
}
