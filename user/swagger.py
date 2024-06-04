CREATE_NEW_USER = """
        ## Create a new user

        Creates a new user with the following details:
        
        - **username**: User's unique username.
        - **email**: User's email address.
        - **first_name**: User's first name.
        - **last_name**: User's last name.
        - **password**: User's password (write-only).
        - **personal_details** (optional): Object containing user's personal details such as phone number, date of birth, and gender.
        - **company_details** (optional): Object containing user's company details such as company name and position.
        - **freelancer_details** (optional): Object containing user's freelancer details such as skills and hourly rate.
        - **addresses** (optional): List of address objects containing street, city, state, postal code, and country.
        
        ### Example Request
        ```json
        {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword",
            "personal_details": {
                "phone_number": "1234567890",
                "date_of_birth": "1990-01-01",
                "gender": "Male"
            },
            "company_details": {
                "company_name": "Example Inc.",
                "position": "Developer"
            },
            "freelancer_details": {
                "skills": "Python, Django",
                "hourly_rate": 50
            },
            "addresses": [
                {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "Anystate",
                    "postal_code": "12345",
                    "country": "USA"
                }
            ]
        }
        ```
        """

UPDATE_AN_EXISTING_USER = """
        ## Update an existing user

        Updates the entire user object. This will replace all fields including personal details, company details, freelancer details, and addresses.

        - **username**: User's unique username.
        - **email**: User's email address.
        - **first_name**: User's first name.
        - **last_name**: User's last name.
        - **password**: User's password (write-only).
        - **personal_details** (optional): Object containing user's personal details such as phone number, date of birth, and gender.
        - **company_details** (optional): Object containing user's company details such as company name and position.
        - **freelancer_details** (optional): Object containing user's freelancer details such as skills and hourly rate.
        - **addresses** (optional): List of address objects containing street, city, state, postal code, and country.

        ### Example Request
        ```json
        {
            "username": "johndoe",
            "email": "johndoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "newsecurepassword",
            "personal_details": {
                "phone_number": "9876543210",
                "date_of_birth": "1990-01-01",
                "gender": "Male"
            },
            "company_details": {
                "company_name": "Example Inc.",
                "position": "Senior Developer"
            },
            "freelancer_details": {
                "skills": "Python, Django, React",
                "hourly_rate": 60
            },
            "addresses": [
                {
                    "id": 1,
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "Anystate",
                    "postal_code": "12345",
                    "country": "USA"
                },
                {
                    "street": "456 Second St",
                    "city": "Othertown",
                    "state": "Otherstate",
                    "postal_code": "67890",
                    "country": "USA"
                }
            ]
        }
        ```
        """

PARTIAL_UPDATE_USER = """
        ## Partially update a user

        Updates parts of the user object. This can be used to update specific fields without affecting other fields.

        - **first_name**: User's first name.
        - **last_name**: User's last name.
        - **addresses** (optional): List of address objects. Each address object can be used to:
            - **Add a New Address**: Include it in the `addresses` array without an `id`.
            - **Update an Existing Address**: Include its `id` in the `addresses` array.
            - **Delete an Address**: Ensure it is not included in the `addresses` array during the update.

        ### Example Request
        ```json
        {
            "first_name": "John",
            "last_name": "Smith",
            "addresses": [
                {
                    "id": 1,
                    "street": "789 New St",
                    "city": "Newtown",
                    "state": "Newstate",
                    "postal_code": "54321",
                    "country": "USA"
                }
            ]
        }
        ```

        ### Managing Addresses
        - **Adding a New Address**: 
        ```json
        {
            "addresses": [
                {
                    "street": "789 New St",
                    "city": "Newtown",
                    "state": "Newstate",
                    "postal_code": "54321",
                    "country": "USA"
                }
            ]
        }
        ```
        - **Updating an Existing Address**: 
        ```json
        {
            "addresses": [
                {
                    "id": 1,
                    "street": "789 Updated St",
                    "city": "Updatedtown",
                    "state": "Updatedstate",
                    "postal_code": "54321",
                    "country": "USA"
                }
            ]
        }
        ```
        - **Deleting an Address**: 
        ```json
        {
            "addresses": [
                {
                    "id": 2,
                    "street": "456 Second St",
                    "city": "Othertown",
                    "state": "Otherstate",
                    "postal_code": "67890",
                    "country": "USA"
                }
            ]
        }
        ```
        By omitting the address with `id: 1`, it will be removed from the user's addresses.
        """