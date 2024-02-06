"""
Object Oriented Programming in Python
"""

class Employee:
    """
    A Class to represent Employee Objects. 
    """

    def __init__(self, **kwargs):
        """A constructor with kwargs dict."""

        self.__name = kwargs.get('name')
        self.__identifier = kwargs.get('identifier')
        self.__salary = kwargs.get('salary')

    @property
    def salary(self):
        """Have salary as a property for the objects. """
        return self.__salary

    @salary.setter
    def salary(self, salary):
        """setter method to set salary and 
        check if it is a positive number, 
        otherwise raise an exception. """

        print("Set year value...")
        if salary > 0:
            self.__salary = float(salary)
        else:
            raise ValueError("Salary must be a positive integer number.")

    @property
    def name(self):
        """Have name as property."""
        return self.__name

    @property
    def identifier(self):
        """Have id as a property."""
        return self.__identifier

    def __str__(self):
        """Have a string representation."""

        return str(self.__class__.__name__) + "\n" + str(self.__name) + \
            ',' + str(self.__identifier) + ',' + str(self.__salary)

############################################################
############################################################
############################################################


class PermanentEmployee(Employee):
    """
    A class to represent Permanent Employee. 
    """

    def __init__(self, **kwargs):
        """A constructor with kwargs dict."""
        super().__init__(**kwargs)
        self.__benefits = kwargs.get('benefits')

    def cal_salary(self):
        """
        Salary Calculation based on different benefits reductions. 
        """
        if self.__benefits == ["health_insurance"]:
            return float(self.salary) * 0.9
        if self.__benefits == ["retirement"]:
            return float(self.salary) * 0.8
        if self.__benefits == ["retirement", "health_insurance"]:
            return float(self.salary) * 0.7

        return float(self.salary)

    @property
    def benefits(self):
        """Have benefits as a property."""
        return self.__benefits

    @benefits.setter
    def benefits(self, benefits):
        """Have setter function for benefits property."""
        self.__benefits = benefits

    def __str__(self):
        """Have a string representation."""
        return Employee.__str__(self) + "," + str(self.__benefits)

class Manager(Employee):
    """
    A Class to represent Managers. 
    """

    def __init__(self, **kwargs):
        """A constructor with kwargs dict."""
        super().__init__(**kwargs)
        self.__bonus = kwargs.get('bonus')

    def cal_salary(self):
        """Calculation of Manager salary based 
        on main salary and bonus payment. 
        """
        return float(self.salary) + float(self.__bonus)

    @property
    def bonus(self):
        """A property for bonus."""
        return self.__bonus

    def __str__(self):
        """Have a string representation."""
        return super().__str__() + "," + str(self.__bonus)



class TemporaryEmployee(Employee):
    """
    A class to represent temporary employee.
    """

    def __init__(self, **kwargs):
        """A constructor with kwargs dict."""
        super().__init__(**kwargs)
        self.hours = kwargs.get('hours')

    def cal_salary(self):
        """A salary calculation for temporal employee."""
        return float(self.salary) * float(self.hours)

    def __str__(self):
        """Have a string representation."""
        return Employee.__str__(self) + "," + str(self.hours)



class Consultant(TemporaryEmployee):
    """
    A Class to represent Consultants. 
    """

    def __init__(self, **kwargs):
        """A constructor with kwargs dict."""
        TemporaryEmployee.__init__(self, **kwargs)
        self.travel = kwargs.get('travel')

    def cal_salary(self):
        """A salary calculation for Consultant employee."""
        return super().cal_salary() + float(self.travel) * 1000

    def __str__(self):
        """Have a string representation."""
        return super().__str__() + "," + str(self.travel)



class ConsultantManager(Consultant, Manager):
    """
    A Class to represent Consultant Managers. 
    """

    def __init__(self,  **kwargs):
        """A constructor with kwargs dict."""
        super().__init__(**kwargs)
        Manager.__init__(self, **kwargs)

    def cal_salary(self):
        """A salary calculation for Consultant Manager employee."""
        return super().cal_salary() + Manager.cal_salary(self) - float(self.salary)

    def __str__(self):
        """Have a string representation."""
        return super().__str__() + "," + Manager.__str__(self)


############################################################
############################################################
############################################################


###### DO NOT CHANGE THE MAIN FUNCTION ########

def main():
    """
    A Main function to create some example objects of our classes. 
    """

    chris = Employee(name="Chris", identifier="UT1")
    print(chris, "\n")

    emma = PermanentEmployee(name="Emma", identifier="UT2",
                              salary=100000, benefits=["health_insurance"])
    print(emma, "\n")

    sam = TemporaryEmployee(name="Sam", identifier="UT3", salary=100,  hours=40)
    print(sam, "\n")

    john = Consultant(name="John", identifier="UT4", salary=100, hours=40, travel=10)
    print(john, "\n")

    charlotte = Manager(name="Charlotte", identifier="UT5",
                        salary=1000000, bonus=100000)
    print(charlotte, "\n")

    matt = ConsultantManager(name="Matt", identifier="UT6",
                              salary=1000, hours=40, travel=4, bonus=10000)
    print(matt, "\n")

    ###################################
    print("Check Salaries")

    print("Emma's Salary is:", emma.cal_salary(), "\n")
    emma.benefits = ["health_insurance"]

    print("Emma's Salary is:", emma.cal_salary(), "\n")
    emma.benefits = ["retirement", "health_insurance"]

    print("Emma's Salary is:", emma.cal_salary(), "\n")

    print("Sam's Salary is:", sam.cal_salary(), "\n")

    print("John's Salary is:", john.cal_salary(), "\n")

    print("Charlotte's Salary is:", charlotte.cal_salary(), "\n")

    print("Matt's Salary is:",  matt.cal_salary(), "\n")


if __name__ == "__main__":
    main()
