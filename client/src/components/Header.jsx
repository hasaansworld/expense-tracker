import React from "react";

const Header = () => {
  return (
    <header className="absolute sticky top-0 w-full z-50 backdrop-blur-md bg-gray-200/10 border-b border-gray-100 w-full">
      <div className="flex items-center justify-center h-16 px-4">
        <a
          href="/"
          className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-600"
        >
          Expense Tracker
        </a>
      </div>
    </header>
  );
};

export default Header;
