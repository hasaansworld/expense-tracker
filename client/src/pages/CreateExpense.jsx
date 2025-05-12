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

      // Check if payer was originally in the participants list
      const payerWasSelected = participants.includes(paidBy);

      // Make sure the payer is included in the participants
      if (!payerWasSelected) {
        participants.push(paidBy);
      }

      // Calculate number of people who should share the expense
      // If payer wasn't selected, only divide among the originally selected users
      const sharingParticipantsCount = payerWasSelected
        ? participants.length
        : participants.length - 1;

      // Calculate equal share for each participant who needs to pay (rounded to 2 decimal places)
      const equalShare =
        sharingParticipantsCount > 0
          ? parseFloat((amount / sharingParticipantsCount).toFixed(2))
          : amount;

      // Check if there's any rounding difference to account for
      let totalShare = equalShare * sharingParticipantsCount;
      let adjustment = parseFloat((amount - totalShare).toFixed(2));

      // Format the participants data
      const participantsData = participants.map((userId, index) => {
        const isPayer = userId === paidBy;

        // Determine share based on whether this user is the payer and if they were originally selected
        let share = equalShare;

        // If this is the payer and they weren't originally selected, their share is 0
        if (isPayer && !payerWasSelected) {
          share = 0;
        }

        // Apply any rounding adjustment to the first non-zero share participant
        if (
          index === 0 &&
          adjustment !== 0 &&
          !(isPayer && !payerWasSelected)
        ) {
          share = parseFloat((equalShare + adjustment).toFixed(2));
        }

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

        // Find the first participant with non-zero share to adjust
        const firstNonZeroIndex = participantsData.findIndex(
          (p) => p.share > 0
        );
        if (firstNonZeroIndex >= 0) {
          participantsData[firstNonZeroIndex].share = parseFloat(
            (
              participantsData[firstNonZeroIndex].share +
              (amount - totalShares)
            ).toFixed(2)
          );
        }
      }

      // Format the final data to send to the backend
      const expenseData = {
        ...formData,
        amount: amount,
        group_id: groupId,
        payer_id: paidBy,
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
