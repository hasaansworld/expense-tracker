# Meetings notes

## Meeting 1.
* **DATE:**
* 30/01/2025
* **ASSISTANTS:**
* Mika Oja

## Minutes:
- **API Overview**: We reviewed the API overview and discussed its description quality. The API was described clearly, but the overall description was somewhat brief.
- **Main Concepts**: The main concepts were thoroughly covered, and the concepts were made clear. However, the diagram representing these concepts could have been more detailed.
- **API Uses**: We discussed how the API is used, and the descriptions provided were clear. The distinction between the client and the service was also well explained.
- **Related Work**: The related work was explained well, with a strong description quality. However, the client example provided was minimal and could be expanded.

## Action Points:
-  Revise the **API Overview** section to provide a more detailed description.
-  Update the **Main Concepts** diagram to include more detailed representations.
-  Provide more examples and clarification for **API Uses** related to the client and service distinction.
-  Expand the **Related Work** section, especially by adding more client examples.





## Meeting 2.
* **DATE:**
* 17/02/2025
* **ASSISTANTS:**
* Mika Oja


## Minutes:
- **Database Design**: The database design was discussed, with emphasis on the use of autoincrement IDs for internal references and UUIDs for exposed identifiers. The database diagram was found to be clear and sufficient.
- **Database Models**: It was confirmed that the models match the design well, but there was a discussion about the relationships. Specifically, we need to define the cascade behavior on relationships, as referenced in exercise 1 regarding "relationship management."
- **Readme**: The Readme file was reviewed, and it was noted that both dependency information and instructions are included, but they could be slightly more detailed for better clarity.

## Action Points:
- Implement autoincrement IDs for internal references and UUIDs for exposed identifiers in the database design.
- Define cascade behavior for the relationships as per the guidelines in exercise 1 for "relationship management."
- Update the Readme file with more detailed dependency information and clearer instructions.





## Meeting 3.
* **DATE:**
* 19/03/2025
* **ASSISTANTS:**
* Mika Oja


## Minutes:
- **Wiki Report**: Discussed the resource table, addressability, and uniform interface. The addressability section needs improvement by unifying the URLs of expense collection and items under one group. The uniform interface section should have validation for PUT requests and unnecessary if statements should be removed from deserialize methods. Statelessness was also confirmed to be good.
- **Basic Implementation**: The project structure and code quality were reviewed. Code quality is good, but there are cyclic imports that should be addressed, as they may cause issues in the future. Documentation and instructions are solid. Test coverage is comprehensive, and the implementation works well.
- **Extras**: The URL converters, schema validation, caching, and authentication were discussed. The schema validation needs to be included in the PUT request as well, and everything else works as expected.

## Action Points:
- Unify the URLs of expense collection and items under one group to improve addressability.
- Add validation for PUT requests and remove unnecessary if statements from deserialize methods in the uniform interface.
- Investigate and resolve cyclic imports in the code to prevent future issues.
- Include schema validation in PUT requests.





## Meeting 4.
* **DATE:**
* 23/04/2025
* **ASSISTANTS:**
* Mika Oja


## Minutes:
- **Documentation**: The documentation was reviewed, and it was noted that the structure needs improvement. It should include schemas and components. Response examples need to be added for the remaining GET requests, and response codes should also include 415 for the wrong media type. Overall, documentation coverage is sufficient.
- **Hypermedia Design**: The state diagram was found to be incomplete. It needs a box for each resource (endpoint), and non-GET actions should not transfer state in the diagram. Custom link relations were covered, but the connectedness of the resources is unclear until the diagram is updated to match the resources.
- **Hypermedia Implementation**: The control implementation was discussed, and it was recommended to use a utility function or class to include hypermedia controls for better reuse and shorter code. However, the implementation doesn’t work currently, and tests are not running. Testing coverage is insufficient.

## Action Points:
- Update the documentation structure to include schemas and components.
- Add response examples for the remaining GET requests in the documentation.
- Add response code 415 for wrong media type in the response codes section.
- Revise the state diagram to include one box for each resource and ensure non-GET actions don’t transfer state.
- Use a utility function/class for the hypermedia controls in the implementation to reduce code repetition and improve reusability.
- Resolve the issues preventing tests from running and improve testing coverage.


## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




