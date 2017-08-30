#include <papi.h>
#include <stdio.h>
#include <stdlib.h>

extern "C" {

    int init(int *eventSet)
    {
        /* Initialize the PAPI library */
        int retval = PAPI_library_init(PAPI_VER_CURRENT);
        // int EventSet = PAPI_NULL;
        // long_long values[1];
        *eventSet = PAPI_NULL;

        if (retval != PAPI_VER_CURRENT && retval > 0) {
            fprintf(stderr, "PAPI library version mismatch!\n");
            return retval;
        }

        if (retval < 0) {
            fprintf(stderr, "Initialization error!\n");
            return retval;
        }

        /* Create the Event Set */
        retval = PAPI_create_eventset(eventSet);
        if ( retval != PAPI_OK) {
            fprintf(stderr, "Eventset creation error %d!\n", retval);
            return retval;
        }

        return 0;

    }


    int add_events(int eventSet, char ** eventNames, int N)
    {
        int retval;
        for (int i = 0; i < N; i++) {
            // printf("Adding event %s\n", eventNames[i]);
            retval = PAPI_add_named_event(eventSet, eventNames[i]);
            if (retval != PAPI_OK) {
                fprintf(stderr, "PAPI event %s was not added, error %d!\n",
                        eventNames[i], retval);
                return retval;
            }
        }
        return 0;
    }


    int start(int eventSet)
    {

        /* Start counting events in the Event Set */
        int retval = PAPI_start(eventSet);
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI start error %d!\n", retval);
            return retval;
        }
        return 0;
    }


    int stop(int eventSet, long long * values)
    {
        /* Stop the counting of events in the Event Set */
        int retval = PAPI_stop(eventSet, values);
        if ( retval != PAPI_OK) {
            fprintf(stderr, "PAPI stop error %d!\n", retval);
            return retval;
        }
        return 0;
    }


    int reset(int eventSet) {
        /* Reset the counting events in the Event Set */
        int retval = PAPI_reset(eventSet);
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI reset error %d!\n", retval);
            return retval;
        }
        return 0;

    }


    int read(int eventSet, long long * values)
    {
        int retval = PAPI_read(eventSet, values);
        /* Read the counting events in the Event Set */
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI Read error %d!\n", retval);
            return retval;
        }
        return 0;
    }

    int destroy(int *eventSet)
    {
        int retval = PAPI_destroy_eventset(eventSet);
        /* Read the counting events in the Event Set */
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI destroy eventset error %d!\n", retval);
            return retval;
        }
        return 0;
    }

}