import "./Header.css";
// import { ICONS, Icon } from "../../components/Icons/Icon";
import { TextButton } from "../../components/Buttons/TextButton/TextButton";
import React from "react";
import { useMediaQuery } from "react-responsive";

export const Header = ({ joinFormRef, aboutRef }) => {
    const smallLayout = useMediaQuery({ maxWidth: 700 });
    const smallLayout1 = useMediaQuery({ maxWidth: 480 });
    const scrollTo = (targetRef, behavior = "smooth") => {
        targetRef.current?.scrollIntoView({
            behavior,
            "block": "start"
        });
    };

    return (
        <div className="header" style={smallLayout1 ? {justifyContent: "center"} : null}>
            {!smallLayout1 && 
                // <Icon iconType={ICONS.MVBoxIcon} width="40" height="40"/>
                <div className="title-text">MV BOX</div>
            }
            <div className="menu">
                <TextButton onClick={() => scrollTo(aboutRef)}>
                    {smallLayout ? "About" : "What the hell is going on here?"}
                </TextButton>
                <TextButton onClick={() => scrollTo(joinFormRef)}>
                    JOIN MV BOX
                </TextButton>
            </div>
        </div>
    );
};