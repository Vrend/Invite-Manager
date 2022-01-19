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
 
 ## Using
 
```
python3 app.py [-d] [-r] [-h]
[-d][--debug]: Debug Mode
[-r][--register]: Enable User Registration
[-h][--help]: Show Usage
```
 
**Warning:** Enabling the debugger may leave you open to exploits.
 
 
 ## Docker Demo
 
 This app has a demo docker image (vrend/invite_manager)
 
 *The docker image may be behind a few commits*
 
 Run it with this command: `docker run -d -p your_port:5000 vrend/invite_manager`
 
## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

*Copyright &copy; 2019 Vrend*
