# Invite-Manager
Manage invites and provide an easy to use QR code for check-in

## Install

Begin by cloning the repository and running the following commands:
 1. `cd Invite-Manager`
 2. `python3 -m venv venv`
 3. `. venv/bin/activate`
 4. `pip install Flask`
 5. `pip install Flask-mysqldb`
 6. `pip install Flask-WTF`
 7. `pip install passlib`
 8. `pip install Flask-QRcode`
 9. `mysql.server start`
 
 This will create a virtual environment and install dependencies
 
 Next you need to create a database in mysql and create a file called 'db-info' in the src directory and fill it out like so
 ```
Line 1: secret key (make it anything)
Line 2: mysql ip (localhost if own machine)
Line 3: mysql username
Line 4: mysql password
Line 5: mysql database name
```
 
 Go ahead and test if everything is working by running the *Flask Testing* configuration in pycharm
 
 ## Running
 
Run the *Flask Production* configuration

If you want to enable debugging, run the *Flask Development* configuration  
**Warning:** Enabling the debugger may leave you open to exploits.
 
 
## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

*Copyright (C) 2019 John Broderick*