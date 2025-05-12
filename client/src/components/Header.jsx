import React, { useState, useEffect } from "react";

const Header = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Check if API key exists in localStorage on component mount
  useEffect(() => {
    const apiKey = localStorage.getItem("api-key");
    setIsLoggedIn(!!apiKey);
  }, []);

  // Handle logout
  const handleLogout = () => {
    // Remove API key from localStorage
    localStorage.removeItem("api-key");

    // Update state
    setIsLoggedIn(false);

    // Redirect to signup page
    window.location.href = "/signup";
  };

  return (
    <header className="sticky top-0 w-full z-50 backdrop-blur-md bg-gray-200/10 border-b border-gray-100">
      <div className="relative flex items-center justify-center h-16 px-4">
        {/* Center title */}
        <a
          href="/"
          className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600"
        >
          Expense Tracker
        </a>

        {/* Position logout button absolutely to the right */}
        {isLoggedIn && (
          <div className="absolute right-4">
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-md bg-red-100 hover:bg-red-200 text-red-800 font-medium transition-colors cursor-pointer"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
