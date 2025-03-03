# CodeAssist Error Handling
*This document is currently a work in progress. However, all error handling standards that have already been established should be followed.*

### **Error Handling Frameworks in Use**

- **Axios Interceptor (Frontend)**:  
   The interceptor logic can be found in `/services/index.js`. Any methods using the `service` object will call backend endpoints within the defined Axios instance, allowing error responses returned by the endpoint to be caught and handled by the error handler within the interceptor (`err => {...}`). Currently, any error responses that contain a `"message"` field in the body will have it returned with `message.error()` to the user.  

  Usage:
  See other files in the `/services` directory for examples of service method implementations.

- **Flask Error Handler (Backend)**:  
  The backend uses a Flask-native error handler, with specific types defined within separate classes in `/utils/errors.py`.
    
  Usage:  
  `raise ConflictError("Whatever message you want in the 'message' field of response.")`

---

### **General Endpoint Guidelines**

- Always check that all necessary response fields or arguments are present at the start of the method, otherwise raise `400 BadRequest`
- Whenever making changes to a database (create, delete, edit), remember to try/catch and rollback in the case of a failure
- When adding with a unique field constraint(s), always query the database first to see if it already exists rather than falling through and allowing the add to fail. Raise `409 ConflictError` in this case.
- Make sure to use error and success codes consistently, [reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)


### **User Message Guidelines (needs to be improved)**

User messages should:
- Be succinct, limited to 1 phrase.
- Not end with a period; commas are discouraged.
- Be specific enough to identify the problem, but avoid sharing any sensitive information.
