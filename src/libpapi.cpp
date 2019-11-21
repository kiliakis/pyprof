#include "papi.h"
#include <stdio.h>
#include <stdlib.h>

extern "C" {

    int init(int *eventSet)
    {
        /* Initialize the PAPI library */
        int retval = PAPI_library_init(PAPI_VER_CURRENT);
        *eventSet = PAPI_NULL;

        if (retval != PAPI_VER_CURRENT && retval > 0) {
            fprintf(stderr, "PAPI version error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }

        if (retval < 0) {
            fprintf(stderr, "PAPI version error\n");

            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        /* Initialize the multiplexed events */
        retval = PAPI_multiplex_init();
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI multiplex init error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }

        /* Create the Event Set */
        retval = PAPI_create_eventset(eventSet);
        if ( retval != PAPI_OK) {
            fprintf(stderr, "PAPI create_eventset error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }

        /* Convert the eventSet */
        retval = PAPI_assign_eventset_component(*eventSet, 0);
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI assign eventSet error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }

        /* Convert the eventSet */
        retval = PAPI_set_multiplex(*eventSet);
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI set multiplex error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }



        return 0;

    }


    int add_events(int eventSet, char ** eventNames, int N)
    {
        int retval;
        for (int i = 0; i < N; i++) {
            retval = PAPI_add_named_event(eventSet, eventNames[i]);
            if (retval != PAPI_OK) {
                // fprintf(stderr, "PAPI add_named_event error\n");
                fprintf(stderr, "PAPI event %s was not added!\n", eventNames[i]);
                PAPI_perror(PAPI_strerror(retval));
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
            fprintf(stderr, "PAPI start error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        return 0;
    }


    int stop(int eventSet, long long * values)
    {
        /* Stop the counting of events in the Event Set */
        int retval = PAPI_stop(eventSet, values);
        if ( retval != PAPI_OK) {
            fprintf(stderr, "PAPI stop error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        return 0;
    }


    int reset(int eventSet) {
        /* Reset the counting events in the Event Set */
        int retval = PAPI_reset(eventSet);
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI reset error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        return 0;

    }


    int read(int eventSet, long long * values)
    {
        int retval = PAPI_read(eventSet, values);
        /* Read the counting events in the Event Set */
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI read error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        return 0;
    }

    int destroy(int *eventSet)
    {
        int retval = PAPI_destroy_eventset(eventSet);
        /* Read the counting events in the Event Set */
        if (retval != PAPI_OK) {
            fprintf(stderr, "PAPI destroy error\n");
            PAPI_perror(PAPI_strerror(retval));
            return retval;
        }
        return 0;
    }

}