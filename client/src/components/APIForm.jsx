import React, { useState, useEffect } from "react";
import HypermediaForm from "./HypermediaForm";

const API_BASE_URL = "http://localhost:5000"; // Update this to your API URL

const UserApi = () => {
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentAction, setCurrentAction] = useState("create"); // 'create' or 'update'
  const [selectedUser, setSelectedUser] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Fetch the API root to discover endpoints
  useEffect(() => {
    const fetchApiRoot = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/`, {
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch API data");
        }

        const data = await response.json();
        setApiData(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchApiRoot();
  }, []);

  // Handle form submission
  const handleFormSubmit = (data) => {
    setSuccessMessage(
      currentAction === "create"
        ? "User created successfully! Your API key has been saved."
        : "User updated successfully!"
    );

    // Refresh data
    setTimeout(() => {
      window.location.reload();
    }, 2000);
  };

  // Handle user selection for update
  const handleUserSelect = (user) => {
    setSelectedUser(user);
    setCurrentAction("update");
  };

  // Reset to creation form
  const handleCreateNew = () => {
    setSelectedUser(null);
    setCurrentAction("create");
    setSuccessMessage(null);
  };

  if (loading) {
    return <div className="p-6 text-center">Loading API data...</div>;
  }

  if (error) {
    return (
      <div className="p-6 text-red-500 border border-red-200 rounded-md bg-red-50">
        Error loading API: {error}
      </div>
    );
  }

  if (successMessage) {
    return (
      <div className="p-6 text-green-600 border border-green-200 rounded-md bg-green-50">
        {successMessage}
        <div className="mt-4">
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded"
            onClick={() => setSuccessMessage(null)}
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto p-6">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-xl font-bold">
          {currentAction === "create" ? "Create New User" : "Update User"}
        </h1>
        {currentAction === "update" && (
          <button
            className="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            onClick={handleCreateNew}
          >
            Create New
          </button>
        )}
      </div>

      {currentAction === "create" &&
        apiData &&
        apiData.controls &&
        apiData.controls.create && (
          <HypermediaForm
            control={apiData.controls.create}
            onSubmit={handleFormSubmit}
            buttonText="Create User"
          />
        )}

      {currentAction === "update" &&
        selectedUser &&
        selectedUser.controls &&
        selectedUser.controls.update && (
          <HypermediaForm
            control={selectedUser.controls.update}
            initialData={selectedUser}
            onSubmit={handleFormSubmit}
            buttonText="Update User"
          />
        )}

      {currentAction === "create" && apiData && apiData.users && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-4">Existing Users</h2>
          <div className="space-y-2">
            {apiData.users.map((user) => (
              <div
                key={user.id}
                className="p-3 border rounded-md hover:bg-gray-50 cursor-pointer flex justify-between items-center"
                onClick={() => handleUserSelect(user)}
              >
                <div>
                  <div className="font-medium">{user.name}</div>
                  <div className="text-sm text-gray-600">{user.email}</div>
                </div>
                <button className="text-blue-500 text-sm">Edit</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserApi;
