import "./BasicLayout.css";
import React from "react";
import { Outlet } from "react-router-dom";

export const BasicLayout = ({ fullHeightPage = false }) => {
  return (
    <div className={`desktop-app-layout ${fullHeightPage ? "full-height" : null}`}>
      <div className="content-block">
        <div className="content">
          <Outlet />
        </div>
      </div>
    </div>
  );
};