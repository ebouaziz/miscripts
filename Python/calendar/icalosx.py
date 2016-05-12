#!/usr/bin/env python2.7

# Experiment various ways to access iCal data on OS X

CALNAME = u'Personal'

scripting_bridge = False
appscript = False
eventkit = True

if scripting_bridge:
    from Foundation import *
    from ScriptingBridge import *
    iCal = SBApplication.applicationWithBundleIdentifier_("com.apple.iCal")
    calendar = None
    for cal in iCal.calendars():
        if cal.name() == CALNAME:
            calendar = cal
            break
    if not calendar:
        raise AssertionError('Cannot select %s calendar', CALNAME.encode('utf8'))
    print calendar.name().encode('utf8', 'ignore')

if appscript:
    from appscript import *
    from datetime import datetime
    calendar = iCal.calendars['Home']
    start_time = datetime(2013,12,01)
    end_time = datetime(2013,12,20)

    for event in calendar.events[(its.start_date >= start_time).AND(its.start_date <= end_time)]():
        event_properties = event.properties()
        print event_properties[k.start_date], event_properties[k.summary]

if eventkit:
    from EventKit import *
    from CalendarStore import *
    store = EKEventStore.alloc().init()
    calendar = store.defaultCalendarForNewEvents()
    print calendar
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
                NSDate.date(), NSDate.dateWithTimeIntervalSinceNow_(3600*24*3), None)
#                NSDate.date(), NSDate.dateWithTimeIntervalSinceNow_(3600*24*3), [calendar])
    for event in store.eventsMatchingPredicate_(predicate):
        print "From %s to %s: %s" % (event.startDate().description(),
                                 event.endDate().description(),
                                 event.title())