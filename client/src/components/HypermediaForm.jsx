import React, { useState } from "react";
import Input from "./Input"; // Assuming we're using the Input component created earlier

const HypermediaForm = ({
  schema,
  onSubmit,
  initialData = {},
  buttonText = "Submit",
  extraFields = "",
}) => {
  const [formData, setFormData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      onSubmit(formData);

      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4 pt-5" onSubmit={handleSubmit}>
      {schema.properties &&
        Object.entries(schema.properties).map(([key, prop]) => {
          // Skip readOnly fields
          if (prop.readOnly) return null;

          // Determine if field is required
          const isRequired = schema.required && schema.required.includes(key);

          // Determine input type
          let inputType = "text";
          if (prop.format === "email") inputType = "email";
          if (prop.format === "password" || key === "password_hash")
            inputType = "password";
          if (prop.type === "number") inputType = "number";

          return (
            <Input
              key={key}
              id={key}
              name={key}
              label={prop.title || key === "password_hash" ? "password" : key}
              type={inputType}
              value={formData[key] || ""}
              onChange={handleChange}
              placeholder={prop.description || ""}
              required={isRequired}
            />
          );
        })}

      {extraFields}

      <div className="pt-2">
        <button
          type="submit"
          className="w-full px-4 py-2 font-medium bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          disabled={loading}
        >
          {loading ? "Processing..." : buttonText}
        </button>
      </div>
      {error && <p className="text-red-500 mt-4">{error}</p>}
    </form>
  );
};

export default HypermediaForm;
