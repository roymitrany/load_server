import subprocess
import sys
from typing import List
num: int = 6

class RequestGenerator:
    """
    This is the main class to holds a data structure for courses
    Since we run this only once, everything is declared in the class level. We do not need
    to instantiate an object (but we can).
    Create the dictionary, and parse the file from which we take the course number index.
    For each course number, add an element to the dictionary. The key for the element is
    the course number, and the value is Course TypedDict object. We only fill the num
    attribute in this new object, and other values are added in separate function, each
    value in its special function.
    """
    process_list: List[subprocess.Popen] = []
    tasks_index: int = 0
    tasks_completed: int = 0

    def generate_request(self):
        process:subprocess.Popen = subprocess.Popen (["python", "http_client.py", str(self.tasks_index)],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        self.process_list.append(process)

        print ("started  task ", self.tasks_index)
        self.tasks_index += 1
        '''while True:
            output = process.stdout.readline ()
            print (output.strip ())
            # Do something else
            return_code = process.poll ()
            if return_code is not None:
                print ('RETURN CODE', return_code)
                # Process has finished, read rest of the output
                for output in process.stdout.readlines ():
                    print (output.strip ())
                break'''

    def simulate(self):
        for i in range (num):
            self.generate_request ()

        while True:
            for i in range (num): # TODO: make it flexible, according to tasks_index
                process = self.process_list[i]
                output = process.stdout.readline ()
                print (output.strip ())
                # Do something else
                return_code = process.poll ()
                if return_code is not None:
                    print ('RETURN CODE', return_code)
                    # Process has finished, read rest of the output
                    for output in process.stdout.readlines ():
                        print (output.strip ())
                    self.tasks_completed += 1
            if self.tasks_completed >=num:
                break


if __name__ == '__main__':
    print("MAIN SIMULATOR !!!!!!!!!!!!")
    req_gen = RequestGenerator()
    req_gen.simulate()
