# CourseRegistrationNotifier

This is a terminal tool I implemented to check the current status (i.e the available seat information) of designated courses. Based on your need, you can search by specific course such CPSC 110 and MATH 200. Or you can also search by department such as CPSC and MATH. Then it will return a JSON reuslt, and if there is an available seat it can also send an email. So, feel free to deploy a cron job to run the script such that you will get notifications once there's an available seat for you!

###  Liberaries Applied 

| Name | Description |
| ----------- | ----------- |
| BeautifoulSoup | parse the HTML elements |
| argparse | define the command-line arguments |
| smtplib | set up SMTP client |


# User Guide
run the executable file with arguments
`Python3 regnotifier args`

## Argument List

### optional arguments
| Argument | Description | Default |
| ----------- | ----------- | ---------- |
| --year | the year in YYYY | the current year | 
| --term | the acdemic term, W for winter term, S for summer term | W |
| --filter | filter the result such that it only outputs course with availble seats  | True |
| --email | the email address that you want the result send to | '' |

### propositional arguments
| Argument | Description | Default |
| ----------- | ----------- | ---------- |
| dept | check a designated department if any section of any course is available. --dept DEPARTNAME e.g --dept CPSC| None |
| course | check a designated course if any section is available. --dept DEPARTNAME --course COURSE_NUMBER e.g --dept CPSC --course 110 | None |
| section | check a designated section of a course. --dept DEPARTNAME --course COURSE_NUMBER --section SECTION_NUMBER e.g --dept CPSC --course 110 --section 001 | None |

## Examples

### If I want to check if CPSC 110 in 2019 winter term still have any seat in any section
`Python3 regnotifier --year 2019 --term W course --dept CPSC --course 110`


### If I want to check if CPSC in 2019 winter term still have any seat in any section of any course
`Python3 regnotifier --year 2019 --term W dept --dept CPSC`

### If I want to check if CPSC 110 in 2019 winter term still have any seat in any section and send the result to abc@gmail.com
`Python3 regnotifier --year 2019 --term W --email abc@gmail.com course --dept CPSC --course 110`
