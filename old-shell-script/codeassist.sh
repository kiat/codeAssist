#!/bin/bash
# https://riptutorial.com/bash/example/29664/request-method--get
# use for example the following http://www.example.com/cgi-bin/script.sh?var1=Hello%20World!&var2=This%20is%20a%20Test.&

# CORS is the way to communicate, so lets response to the server first
echo "Content-type: text/html"    # set the data-type we want to use
echo ""    # we dont need more rules, the empty line initiate this.
# CORS are set in stone and any communication from now on will be like reading a html-document.
# Therefor we need to create any stdout in html format!
# create html scructure and send it to stdout
echo "<!DOCTYPE html>"
echo "<html><head>  <meta charset=\"UTF-8\"> "


# The content will be created depending on the Request Method 
if [ "$REQUEST_METHOD" = "GET" ]; then
    # Note that the environment variables $REQUEST_METHOD and $QUERY_STRING can be processed by the shell directly. 
    # One must filter the input to avoid cross site scripting.
    User=$(echo "$QUERY_STRING" | sed -n 's/^.*User=\([^&]*\).*$/\1/p')    # read value of "User"
    User_Dec=$(echo -e $(echo "$user" | sed 's/+/ /g;s/%\(..\)/\\x\1/g;'))    # html decode

    Nr=$(echo "$QUERY_STRING" | sed -n 's/^.*Nr=\([^&]*\).*$/\1/p')
    Nr_Dec=$(echo -e $(echo "$Var2" | sed 's/+/ /g;s/%\(..\)/\\x\1/g;'))

    Feedback=$(echo "$QUERY_STRING" | sed -n 's/^.*Feedback=\([^&]*\).*$/\1/p')
    # Nr_Dec=$(echo -e $(echo "$Var2" | sed 's/+/ /g;s/%\(..\)/\\x\1/g;'))

    Course=$(echo "$QUERY_STRING" | sed -n 's/^.*Course=\([^&]*\).*$/\1/p')

    Lang=$(echo "$QUERY_STRING" | sed -n 's/^.*Lang=\([^&]*\).*$/\1/p')

    Compilecheck=$(echo "$QUERY_STRING" | sed -n 's/^.*CompileCheck=\([^&]*\).*$/\1/p')


    # create content for stdout
    echo "<title>Compule and Test Run Results</title>"
    echo "</head><body>"
    echo "<h1>This is the CodeAssist System.</h1>"
    echo "<h2>Here is CodeAssist Feedback about your implementation.</h2>"
    echo "<h3>User=${User} </h3>"    # print the values to stdout
    echo "<h3>Assignment=${Nr} </h3>"    # print the values to stdout
    echo "<h3>Feedback=${Feedback} </h3>"    # p

#   echo "<p>QUERY_STRING: ${QUERY_STRING}<br>var1=${User_Dec}<br>var2=${User_Dec}</p>"    # print the values to stdout


# User repository name
repo=$(echo "met-cs665-$Nr-$User")

# Course Selected
echo "<h3>Course=$Course </h3>"

# Course CS521 is not implemented yet.
if [ "$Course" = "cs521" ]; then
	echo "<h2><font color="red"> System for course 521 is not implemented yet.  </font> </h2>"
	exit 0
fi


# Lang Selected
echo "<h3>Programming Language=$Lang </h3>"

# Course CS521 is not implemented yet.
if [ "$Lang" = "Python" ]; then
	echo "<h2><font color="red"> System for Python Programming Language is not implemented yet.  </font> </h2>"
	exit 0
fi




# result=$(mkdir "$repo" )
echo "<h2><font color="blue"> Repository Name is git@github.com:metcs/${repo}.git </font> </h2>"


result=$(cd sessions && rm -rf "$repo" )
echo "<p>${result}</p>"

result=$(cd sessions && git clone "git@github.com:metcs/$repo.git" || echo 0)
# result=$( whoami  || echo 0)

# echo "<p>result=${result}</p>"

# This is check to know if the reposotry could be successfully cloned
if [ "$result" == "0" ]; then
	echo "<h1><font color="red">  NO SUCH Github Repository EXIST! <br/> Please enter the correct Github account name or the assignment number. </font> </h1>"
	exit 0 
fi


echo "<h3>Cloned your repository and run the following Maven command:</h3>"



if [[ "${Feedback}" == "build" ]]; then
# result=$(cd sessions&& cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile test checkstyle:check  kupusoglu.orhan:sloc-maven-plugin:sloc)
	result=$(cd sessions && cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile | ansi2html -n -w -c)
	echo "<h1>timeout 60 mvn clean compile </h1>"
elif  [[ "${Feedback}" == "tests" ]]; then
	result=$(cd sessions && cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile test | ansi2html -n -w -c )
	echo "<h1>timeout 60 mvn clean compile test </h1>"

elif  [[ "${Feedback}" == "spotbugs" ]]; then
	result=$(cd sessions && cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile spotbugs:check | ansi2html -n -w -c )
	 echo "<h1>timeout 60 mvn clean compile spotbugs:check </h1>"

elif  [[ "${Feedback}" == "stylegoogle" ]]; then
	result=$(cd sessions && cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile checkstyle:check | ansi2html -n -w -c )
        echo "<h1>timeout 60 mvn clean compile checkstyle:check </h1>"

elif  [[ "${Feedback}" == "stats" ]]; then
	result=$(cd sessions && cd "met-cs665-$Nr-$User"  && timeout 60 mvn clean compile kupusoglu.orhan:sloc-maven-plugin:sloc | ansi2html -n -w -c )
        echo "<h1>timeout 60 mvn clean compile kupusoglu.orhan:sloc-maven-plugin:sloc </h1>"


elif  [[ "${Feedback}" == "classdep" ]]; then
	# result="This feature will be implemented soon. " )
        echo "<h1>This feature will be implemented soon. Please check this feature later... </h1>"

elif  [[ "${Feedback}" == "codeexe" ]]; then
	# result="This feature will be implemented soon. " )
        echo "<h1>This feature will be implemented soon. Please check this feature later... </h1>"

elif  [[ "${Feedback}" == "profilemem" ]]; then
	# result="This feature will be implemented soon. " )
        echo "<h1>This feature will be implemented soon. Please check this feature later... </h1>"

elif  [[ "${Feedback}" == "performance" ]]; then
	# result="This feature will be implemented soon. " )
        echo "<h1>This feature will be implemented soon. Please check this feature later... </h1>"

elif  [[ "${Feedback}" == "similarcode" ]]; then
	# result="This feature will be implemented soon. " )
        echo "<h1>This feature will be implemented soon. Please check this feature later... </h1>"

fi

# filestore=$(echo $result  > file.txt )

echo "<h2></h2>"

#

# newResult =$(echo "${result//$'\n'/<br />}")

# newResult=`echo $finalResult | tr '[:upper:]' '[:lower:]'`

result=$(echo "${result//$'\n'/<br />}")
echo "<p> ${result} </p>"


fileresult=$(cd outputs && date  >> "$repo.txt"  && echo "<br/><br/><br/><br/><br/>  $result" >> "$repo.txt" )
# echo "<p>${result}</p>"



else

    echo "<title>456 Wrong Request Method</title>"
    echo "</head><body>"
    echo "<h1>456</h1>"
    echo "<p>Requesting data went wrong.<br>The Request method has to be \"GET\" only!</p>"

fi

echo "<hr>"
echo "$SERVER_SIGNATURE"    # an other environment variable
echo "</body></html>"    # close html

exit 0



