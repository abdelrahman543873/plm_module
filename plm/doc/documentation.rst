the module is composed of 5 modules and views and a wizard , each models is gonna be explained briefly with
the functionality of each function written down and why the choice was made

the log module :
==============================

the log module is used to document each process for each product and it's used to store different attributes

the attributes are
--------------------------

name : stores the name of the process
part : stores the parts required for each process
value : stores the amount the material used in each process
difference : used to store the difference between the standard template of the process and the actual parts
taken by the process
time : used to store time taken by each process
worker_name : used to store the name of the workers who executed the process
cost : for storing the total value of each process including two factors which are the cost of the material
and the cost of the worker time
time_difference : used to store the difference between the standard timing required for each process and the
actual time that was taken by the process
notes : used to store any notes after each process is done
rating : used to give each process a rating based on the admin of the process

the process model:
==============================

used to store the templates of each process to compare between the actual process and the standard process
in mind and it stores the following

attributes
------------

name: the name of the process
time : the time taken by the process
process_parts : a one2many field that is used to store the amounts of each material that is used for the proces
, notice this field is connected to an intermediate model "process.parts" in order to be able to store the
quantities , because if you link it directly to the inventory table you can't store variable quantites for
each raw material
workers : are the workers that should be working on this process
output : is the output of each process
quantity: is the quantity of the output produced by the process

functions :
--------------

check_quantity: checking to see if an output was selected and at the same time 0 quantity was in the quantity
field and in this case an error is raised
checking_parts_repetition : checks if the user selects more than one of the same product and in this case an
error is released
check_quantity: checking if the quantity of each part that was selected for the process equal to 0  and raising
an error in that case

then a sql constraint is added to prevent a duplication of the process

process.parts model
=======================

a model that is intermediate between any model and the inventory model and it allows the selection of a material
and the preferred quantity

fields :
----------

name: a many to one field that allows the selection of the inventory parts
quantity: the amount of the material required
process_parts : connects between the process table and the inventory.parts
forum_actual_parts : is the parts that is taken actually by each process
forum_standard_parts : the standard amount of parts that is usually taken by each process