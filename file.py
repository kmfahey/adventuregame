print("")
print("          === Automated Teller Machine ===          ")
name = input("Enter name to register: ")
pin = input("Enter Pin: ")
balance = 0
print(f"{name} has been registered with a starting balance of ${balance}")
print()
def atm_menu(name):
    while True:
        (print)
        print("          === Automated Teller Machine ===          ")
        print("LOGIN")
        name_to_validate = input("Enter name: ")
        pin_to_validate = input("Enter PIN:")
        if name_to_validate == name and pin_to_validate == pin:
            print("Login successful!")
            break
        else:
            print("Invalid credentials!")
    """while true:
        print("User: " + name)
        print("------------------------------------------")
        print("| 1.    Balance     | 2.    Deposit      |")
        print("------------------------------------------")
        print("------------------------------------------")
        print("| 3.    Withdraw    | 4.    Logout       |")
        print("------------------------------------------")
        option = input("Choose an option:")"""

atm_menu("name")


