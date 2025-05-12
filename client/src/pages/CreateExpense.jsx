import Card from "../components/Card";
import HypermediaForm from "../components/HypermediaForm";
import HypermediaClient from "../hypermedia";
import { useEffect, useState } from "react";
import { useParams } from "react-router";

const client = new HypermediaClient();
export default function CreateExpense() {
  const { groupId } = useParams();

  const [members, setMembers] = useState([]);
  const [schema, setSchema] = useState({});
  const [error, setError] = useState("");
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [paidBy, setPaidBy] = useState("");

  useEffect(() => {
    async function navigateHypermedia() {
      // Initialize and load routes
      await client.navigateToRoot();
      const groupMembersResponse = client.getResourceEndpoint(
        "Group Member",
        "GET"
      );
      const groupMembers = await client.navigateToUrl(
        groupMembersResponse.replace("<group_id>", groupId),
        "GET"
      );
      console.log("Group Members Response:", groupMembers);
      setMembers(groupMembers.members);
      setPaidBy(groupMembers.members[0].user_id); // Default to the first member
      await client.navigateToRoot();
      const expensesResponse = await client.navigateToResource(
        "Expense",
        "GET",
        {
          group_id: groupId,
        }
      );
      console.log("Expenses Response:", expensesResponse);
      const createSchema = client.extractSchemaFromResponse(
        expensesResponse,
        "create"
      );
      setSchema(createSchema);
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

  const handleFormSubmit = async (formData) => {
    // Validate that at least one user is selected
    if (selectedUsers.length === 0) {
      setError("Please select at least one user to split the expense with.");
      return;
    }

    try {
      // Make sure paidBy is valid
      if (!paidBy) {
        setError("Please select who paid for this expense.");
        return;
      }

      // Ensure the amount field is present and is a valid number
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        setError("Please enter a valid expense amount.");
        return;
      }

      // Create a copy of selected users to work with
      let participants = [...selectedUsers];

      // Make sure the payer is included in the participants
      if (!participants.includes(paidBy)) {
        participants.push(paidBy);
      }

      // Calculate equal share for each participant (rounded to 2 decimal places)
      const equalShare = parseFloat((amount / participants.length).toFixed(2));

      // Check if there's any rounding difference to account for
      let totalShare = equalShare * participants.length;
      let adjustment = parseFloat((amount - totalShare).toFixed(2));

      // Format the participants data
      const participantsData = participants.map((userId, index) => {
        // Apply any rounding adjustment to the first participant to ensure total equals amount
        let share = equalShare;
        if (index === 0 && adjustment !== 0) {
          share = parseFloat((equalShare + adjustment).toFixed(2));
        }

        const isPayer = userId === paidBy;
        return {
          user_id: userId,
          share: share,
          paid: isPayer, // The person who paid has already paid their share
        };
      });

      // Verify the total shares equal the expense amount
      const totalShares = participantsData.reduce((sum, p) => sum + p.share, 0);
      if (Math.abs(totalShares - amount) > 0.01) {
        console.warn(
          `Share calculation rounding issue: ${totalShares} vs ${amount}`
        );
        // Adjust the first participant's share to make it exactly match
        participantsData[0].share = parseFloat(
          (participantsData[0].share + (amount - totalShares)).toFixed(2)
        );
      }

      // Format the final data to send to the backend
      const expenseData = {
        ...formData,
        amount: amount, // Ensure amount is a string for the backend
        group_id: groupId,
        payer_id: paidBy, // Add the payer ID
        participants: participantsData,
      };

      console.log("Submitting expense data:", expenseData);

      // Call your API to create the expense
      await client.navigateToRoot();
      const response = await client.executeResourceOperation(
        "Expense",
        "POST",
        { group_id: groupId },
        expenseData
      );

      console.log("Expense created successfully:", response);

      // Redirect to the group expenses page or show success message
      window.location.href = `/groups/${groupId}`;
    } catch (err) {
      console.error("Error creating expense:", err);
      setError(err.message || "Failed to create expense. Please try again.");
    }
  };

  return (
    <div className="p-20 w-full h-full flex flex-col items-center">
      <Card className="w-[400px]">
        <h1 className="text-2xl font-semibold">Create New Expense</h1>
        {schema && (
          <HypermediaForm
            schema={schema}
            buttonText="Create Expense"
            onSubmit={handleFormSubmit}
            className="mt-6"
            extraFields={
              <div>
                <div className="mb-4">
                  <label
                    htmlFor="paidBy"
                    className="block text-sm font-medium text-gray-700 mb-1 text-start"
                  >
                    Paid by <span className="text-red-500 ml-1">*</span>
                  </label>

                  <select
                    id="paidBy"
                    name="paidBy"
                    value={paidBy}
                    onChange={(e) => setPaidBy(e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base  border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                    required
                  >
                    <option value="" disabled>
                      Select who paid
                    </option>
                    {members.map((member) => (
                      <option key={member.user_id} value={member.user_id}>
                        {member.name || member.user_name}
                      </option>
                    ))}
                  </select>
                </div>
                <p className="block text-sm font-medium text-gray-700 mb-1 text-start">
                  Split between <span className="text-red-500 ml-1">*</span>
                </p>
                {members.map((user) => (
                  <div
                    key={user.id}
                    className="flex gap-4 items-start border-t border-gray-100 p-4 hover:bg-gray-50 rounded-md"
                  >
                    <input
                      type="checkbox"
                      id={`user-${user.user_id}`}
                      className="h-5 w-5 text-blue-600 rounded"
                      checked={selectedUsers.includes(user.user_id)}
                      onChange={() => handleCheckboxChange(user.user_id)}
                    />
                    <label
                      htmlFor={`user-${user.id}`}
                      className="ml-3 flex-1 cursor-pointer flex items-start"
                    >
                      <div className="text-start">
                        <p className="font-medium">{user.user_name}</p>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            }
          />
        )}
        {error && <div className="text-red-500 mt-4">{error}</div>}
      </Card>
    </div>
  );
}
