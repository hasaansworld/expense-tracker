import { useEffect, useState } from "react";
import Card from "../components/Card";
import HypermediaClient from "../hypermedia";
import HypermediaForm from "../components/HypermediaForm";

const client = new HypermediaClient();
export default function CreateGroup() {
  const [schema, setSchema] = useState({});

  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const groupsResponse = await client.navigateToResource("Group", "GET");
      const createSchema = client.extractSchemaFromResponse(
        groupsResponse,
        "create"
      );
      setSchema(createSchema);
    }
    navigateHypermedia();
  }, []);

  const handleFormSubmit = async (formData) => {
    console.log("Form submitted with data:", formData);
    const response = await client.executeControl("create", formData);
    if (response) {
      console.log("Response:", response);
      window.location.href = response["@controls"].self.href; // Redirect to the main page
    }
  };

  return (
    <div className="p-20 w-full h-full flex flex-col items-center justify-center">
      <Card className="w-[400px]">
        <h1 className="text-2xl font-semibold">Create New Group</h1>
        <p className="mt-2 text-gray-500">
          Let's create a new group for tracking expenses.
        </p>
        {schema && (
          <HypermediaForm
            schema={schema}
            onSubmit={handleFormSubmit}
            buttonText="Create Group"
            className="mt-6"
          />
        )}
      </Card>
    </div>
  );
}
