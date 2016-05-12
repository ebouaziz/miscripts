#!/usr/bin/env python

# Experiment with a JTAG TAP controller state machine

class State(object):
    """
    """
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def setx(self, fstate, tstate):
        self.exits = [fstate, tstate]


class StateMachine(object):
    """
    """
    def __init__(self):
        self.states = {}
        for s in ['test_logic_reset',
                  'run_test_idle',
                  'select_dr_scan',
                  'capture_dr',
                  'shift_dr',
                  'exit_1_dr',
                  'pause_dr',
                  'exit_2_dr',
                  'update_dr',
                  'select_ir_scan',
                  'capture_ir',
                  'shift_ir',
                  'exit_1_ir',
                  'pause_ir',
                  'exit_2_ir',
                  'update_ir']:
            self.states[s] = State(s)
        self['test_logic_reset'].setx(self['run_test_idle'], 
                                      self['test_logic_reset'])
        self['run_test_idle'].setx(self['run_test_idle'], 
                                   self['select_dr_scan'])
        self['select_dr_scan'].setx(self['capture_dr'], 
                                   self['select_ir_scan'])
        self['capture_dr'].setx(self['shift_dr'], self['exit_1_dr'])
        self['shift_dr'].setx(self['shift_dr'], self['exit_1_dr'])
        self['exit_1_dr'].setx(self['pause_dr'], self['update_dr'])
        self['pause_dr'].setx(self['pause_dr'], self['exit_2_dr'])
        self['exit_2_dr'].setx(self['shift_dr'], self['update_dr'])
        self['update_dr'].setx(self['run_test_idle'], 
                               self['select_dr_scan'])
        self['select_ir_scan'].setx(self['capture_ir'], 
                                    self['test_logic_reset'])
        self['capture_ir'].setx(self['shift_ir'], self['exit_1_ir'])
        self['shift_ir'].setx(self['shift_ir'], self['exit_1_ir'])
        self['exit_1_ir'].setx(self['pause_ir'], self['update_ir'])
        self['pause_ir'].setx(self['pause_ir'], self['exit_2_ir'])
        self['exit_2_ir'].setx(self['shift_ir'], self['update_ir'])
        self['update_ir'].setx(self['run_test_idle'], self['select_dr_scan'])
                             
        self._current = self['test_logic_reset']
    
    def __getitem__(self, name):
        return self.states[name]
        
    def find_best_path(self, from_, to):
        source = self[from_]
        target = self[to]
        paths = []
        def next_path(state, target, path):
            # this test match the target, path is valid
            if state == target:
                return path+[state]
            # candidate paths
            paths = []
            for n,x in enumerate(state.exits):
                # next state is self (loop around), kill the path
                if x == state:
                    continue
                # next state already in upstream (loop back), kill the path
                if x in path:
                    continue
                # try the current path
                npath = next_path(x, target, path + [state])
                # downstream is a valid path, store it
                if npath:
                    paths.append(npath)
            # keep the shortest path
            return paths and min([(len(l), l) for l in paths], 
                                  key=lambda x: x[0])[1] or []
        return next_path(source, target, [])
        
    def get_events(self, path):
        events = []
        for s,d in zip(path[:-1], path[1:]):
            for e,x in enumerate(s.exits):
                if x == d:
                    events.append(e)
        if len(events) != len(path) - 1:
            raise AssertionError("Invalid path")
        return events
    
if __name__ == '__main__':
    sm = StateMachine()
    #path = sm.find_best_path('exit_2_ir', 'pause_ir')
    #print path
    path = sm.find_best_path('capture_dr', 'exit_1_ir')
    print path
    events = sm.get_events(path)
    print events