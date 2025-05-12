import Card from "../components/Card";
import HypermediaClient from "../hypermedia";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

const client = new HypermediaClient();
export default function AddMembers() {
  const { groupId } = useParams();

  const [group, setGroup] = useState({});
  const [missingUsers, setMissingUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const groupsResponse = await client.navigateToResource("Group", "GET");
      const url = groupsResponse["@controls"].self.href;
      const groupResponse = await client.navigateToUrl(
        `/api${url}${groupId}`,
        "GET"
      );
      console.log("Group Response:", groupResponse);
      setGroup(groupResponse);
      await client.navigateToRoot();
      const groupMembersResponse = client.getResourceEndpoint(
        "Group Member",
        "GET"
      );
      const groupMembers = await client.navigateToUrl(
        groupMembersResponse.replace("<group_id>", groupId),
        "GET"
      );
      await client.navigateToRoot();
      const userResponse = await client.navigateToResource("User", "GET");
      const allUsers = userResponse.users;
      const missingUsers = allUsers.filter((user) => {
        return !groupMembers.members.some(
          (member) => member.user_id === user.id
        );
      });
      setMissingUsers(missingUsers);
      console.log("Missing Users:", missingUsers);
    }
    if (groupId) navigateHypermedia();
  }, [groupId]);

  const handleCheckboxChange = (userId) => {
    setSelectedUsers((prev) => {
      if (prev.includes(userId)) {
        return prev.filter((id) => id !== userId);
      } else {
        return [...prev, userId];
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (selectedUsers.length === 0) {
      setError("Please select at least one user to add");
      return;
    }

    console.log("Selected Users:", selectedUsers);

    try {
      setSubmitting(true);
      setError("");

      await client.navigateToRoot();
      const membersEndpoint = client.getResourceEndpoint(
        "Group Member",
        "POST"
      );
      console.log("Members Endpoint:", membersEndpoint);
      // Add each selected user to the group
      for (const userId of selectedUsers) {
        const result = await client.executeResourceOperation(
          "Group Member",
          "POST",
          { group_id: groupId },
          { user_id: userId }
        );
        console.log(`Added user ${userId} to group:`, result);
      }

      window.location.href = `/groups/${groupId}`; // Redirect to the group page
    } catch (err) {
      console.error("Error adding members:", err);
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-20">
      <Card className="w-[400px] mx-auto">
        <h1 className="text-2xl font-semibold">Add Members</h1>
        <p className="mt-2 text-gray-500">Add new members to {group.name}</p>
        <form onSubmit={handleSubmit} className="mt-6">
          <div className="smb-6 w-[300px] mx-auto">
            {missingUsers.map((user) => (
              <div
                key={user.id}
                className="flex gap-4 items-start border-t border-gray-100 p-4 hover:bg-gray-50 rounded-md"
              >
                <input
                  type="checkbox"
                  id={`user-${user.id}`}
                  className="h-5 w-5 text-blue-600 rounded"
                  checked={selectedUsers.includes(user.id)}
                  onChange={() => handleCheckboxChange(user.id)}
                />
                <label
                  htmlFor={`user-${user.id}`}
                  className="ml-3 flex-1 cursor-pointer flex items-start"
                >
                  <div className="text-start">
                    <p className="font-medium text-xl">{user.name}</p>
                    <p className="text-gray-600 text-sm">{user.email}</p>
                  </div>
                </label>
              </div>
            ))}
          </div>
          <button
            type="submit"
            className="w-[300px] mt-6 cursor-pointer px-4 py-2 font-bold bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            disabled={submitting}
          >
            {submitting ? "Processing..." : "Add Members"}
          </button>
          {error && <div className="text-red-500 mt-4">{error}</div>}
        </form>
      </Card>
    </div>
  );
}
