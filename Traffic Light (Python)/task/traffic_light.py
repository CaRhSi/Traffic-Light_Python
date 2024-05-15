import os
import threading
import time

# Global constants for menu options
MENU_OPTION_ADD_ROAD = 1
MENU_OPTION_DELETE_ROAD = 2
MENU_OPTION_SYSTEM_STATUS = 3
MENU_OPTION_QUIT = 0

# ANSI color codes
ANSI_RED = "\u001B[31m"
ANSI_GREEN = "\u001B[32m"
ANSI_YELLOW = "\u001B[33m"
ANSI_RESET = "\u001B[0m"


class QueueThread(threading.Thread):
    def __init__(self, interval, system_startup_time, max_roads):
        super().__init__()
        self.just_changed = None
        self.interval = interval
        self.running = False
        self.system_startup_time = system_startup_time
        self.print_system_info = False  # Flag to control printing system information
        # Queue to store roads
        self.queue = []
        self.queue_length = 0
        self.num_roads = max_roads  # Maximum number of roads
        self.interval_timer = 0
        self.open_time = 0

    def run(self):
        self.running = True
        while self.running:
            # Increase the variable for the amount of time since system startup
            self.system_startup_time += 1  # Assuming seconds
            self.interval_timer += 1
            if self.interval_timer == self.interval:
                self.interval_timer = 0
            if self.print_system_info:
                self.system_information_output()
            self.timing_loop()
            time.sleep(1)

    def input_check(self):
        user_input = input()
        if user_input == '' or user_input == '\n':
            self.print_system_info = False
        return

    def stop(self):
        self.running = False

    def timing_loop(self):
        self.just_changed = False  # Tracks if the open road has just been changed to handle edge cases
        open_index = self.find_open_road_index()

        if open_index is not None:
            self.open_time += 1
            nri = (open_index + 1) % self.queue_length
            if self.queue[open_index]["time_remaining"] <= 1 < self.queue_length and not self.just_changed:
                self.queue[open_index]["state"] = "closed"
                self.queue[nri]["state"] = "open"
                self.open_time = 0
                self.queue[nri]["time_remaining"] = self.interval
                self.just_changed = True
            elif self.queue[open_index]["time_remaining"] <= 1 and self.queue_length == 1:
                self.queue[open_index]["state"] = "open"
                self.open_time = 0
                self.queue[open_index]["time_remaining"] = self.interval
            else:
                self.queue[open_index]["time_remaining"] -= 1

        # Find the open roads index
        open_index = self.find_open_road_index()
        # Enumerate over the queue. Based on the open roads time_rem determine the rest of the roads time_rem
        for i, road in enumerate(self.queue):
            its_from_open = (i - open_index) % self.queue_length
            if its_from_open == 0:
                road["time_remaining"] = self.queue[open_index]["time_remaining"]
            else:
                road["time_remaining"] = self.queue[open_index]["time_remaining"] + (self.interval * (its_from_open - 1))

    def find_open_road_index(self):
        for i, road in enumerate(self.queue):
            if road["state"] == "open":
                return i
        return None

    def system_information_output(self):
        # Print system information
        print(f"! {self.system_startup_time}s. have passed since system startup !")
        print(f"! Number of roads: {self.num_roads} !")
        print(f"! Interval: {self.interval} !")
        print('')
        for road in self.queue:
            if road["name"] is not None:
                state_color = ANSI_GREEN if road["state"] == "open" else ANSI_RED
                state_info = "open" if road["state"] == "open" else "closed"
                print(
                    f'{state_color}Road "{road["name"]}" will be {state_info} for {road["time_remaining"]}s.{ANSI_RESET}')
        print(f'! Press "Enter" to open menu !')

    def add_road(self, road_name):
        new_road = {"name": road_name, "state": "closed", "time_remaining": self.interval}
        if self.queue_length >= self.num_roads:
            print("Queue is full. Cannot add more roads.")
            return

        # Add the new road
        self.queue.append(new_road)
        self.queue_length += 1

        # Find the index of the currently open road
        open_index = self.find_open_road_index()


        # Calculate the distance from the open road
        if open_index is not None:
            its_from_open = (len(self.queue) - 1) - open_index
            time_rem = self.queue[open_index]["time_remaining"]
        else:
            its_from_open = 0

        if its_from_open == 1:
            self.queue[-1]["time_remaining"] = time_rem
        elif its_from_open > 1:
            self.queue[-1]["time_remaining"] = time_rem + (self.interval * (its_from_open - 1))
        # Make the new road open if there are no other open roads
        if open_index is None:
            self.queue[-1]["state"] = "open"
            self.queue[-1]["time_remaining"] = self.interval

    def delete_road(self):
        if self.queue_length == 1:
            print(f'{self.queue[0]["name"]} deleted!')
            self.queue.pop(0)
            self.queue_length -= 1
        elif self.queue_length > 1:
            # If the first road is open, make the next road open and update its timing
            if self.queue[0]["state"] == "open":
                self.queue[1]["state"] = "open"
                self.queue[1]["time_remaining"] = self.interval
            # Delete the first road
            print(f'{self.queue[0]["name"]} deleted!')
            self.queue.pop(0)
            self.queue_length -= 1
        elif self.queue_length == 0:
            print("Queue is empty. No roads to delete.")


def main():
    input_turn = 2
    input_message_roads = "Input the number of roads: "
    input_message_interval = "Input the interval: "
    end_p1 = False
    print("Welcome to the Traffic Management System!")

    while not end_p1:
        if (input_turn % 2) == 0:
            try:
                num_roads = int(input(input_message_roads))
                if num_roads <= 0:
                    raise ValueError
                input_turn += 1
            except ValueError:
                input_message_roads = ""  # Clear input message after unsuccessful input
                print('Error! Incorrect Input. Try again: ', end="")
                continue
        if (input_turn % 2) != 0:
            try:
                interval = int(input(input_message_interval))
                if interval <= 0:
                    raise ValueError
                end_p1 = True
                input_turn += 1
            except ValueError:
                print('Error! Incorrect Input. Try again: ', end="")
                input_message_interval = ""  # Clear input message after unsuccessful input
                continue

    # Create and start the QueueThread after settings are provided
    system_startup_time = 0  # Initialize system startup time
    queue_thread = QueueThread(interval, system_startup_time, num_roads)
    queue_thread.setName("QueueThread")
    queue_thread.start()

    # Loop for the menu
    while True:
        print("Menu:")
        print("1. Add road")
        print("2. Delete road")
        print("3. System status and running time")
        print("0. Quit")

        try:
            option = int(input())
            if option not in [MENU_OPTION_QUIT, MENU_OPTION_ADD_ROAD, MENU_OPTION_DELETE_ROAD, MENU_OPTION_SYSTEM_STATUS]:
                raise ValueError
        except ValueError:
            print("Incorrect option")
            os.system('cls' if os.name == 'nt' else 'clear')
            input()
            continue

        if option == MENU_OPTION_QUIT:
            print("Exiting the Traffic Management System. Goodbye!")
            queue_thread.stop()
            queue_thread.join()
            break
        elif option == MENU_OPTION_ADD_ROAD:
            if num_roads is None:
                print("Please input the number of roads first.")
                continue
            road_name = input("Input the name of the road: ")
            if queue_thread.queue_length >= num_roads:
                print("Queue is full. Cannot add more roads.")
            elif queue_thread.queue_length < num_roads:
                queue_thread.add_road(road_name)
                print(f"{road_name} Added!")
            input()
            continue
        elif option == MENU_OPTION_DELETE_ROAD:
            if num_roads is None:
                print("Please input the number of roads first.")
                continue
            queue_thread.delete_road()
            input()
            continue
        elif option == MENU_OPTION_SYSTEM_STATUS:
            # Set print_system_info to True
            queue_thread.print_system_info = True
            input_thread = threading.Thread(target=queue_thread.input_check)
            input_thread.start()
            # Wait for the input thread to finish before clearing the screen
            input_thread.join()
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
            continue

    return

if __name__ == "__main__":
    main()


