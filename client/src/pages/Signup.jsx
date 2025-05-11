import { useEffect, useState } from "react";
import Card from "../components/Card";
import HypermediaClient from "../hypermedia";
import HypermediaForm from "../components/HypermediaForm";

const client = new HypermediaClient();
export default function Signup() {
  const [schema, setSchema] = useState({});
  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const response = await client.navigateToResource("User", "GET");
      const createSchema = client.extractSchemaFromResponse(response, "create");
      setSchema(createSchema);
      console.log("Create Schema:", createSchema);
    }
    navigateHypermedia();
  }, []);

  const handleFormSubmit = async (formData) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(formData.password_hash);

    // Hash using SHA-256
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    formData.password_hash = hashHex;

    console.log("Form submitted with data:", formData);
    const response = await client.executeControl("create", formData);
    if (response) {
      window.location.href = "/"; // Redirect to the main page
    }
  };

  return (
    <div className="p-20 w-full h-full flex flex-col items-center justify-center">
      <Card className="w-[400px]">
        <h1 className="text-2xl font-semibold">Signup</h1>
        <p className="mt-2 text-gray-500">Create an account to continue</p>
        {schema && (
          <HypermediaForm
            schema={schema}
            onSubmit={handleFormSubmit}
            className="mt-6"
          />
        )}
      </Card>
    </div>
  );
}
