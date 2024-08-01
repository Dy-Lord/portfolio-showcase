import { useMediaQuery } from "react-responsive";
import { ICONS, Icon } from "../../components/Icons/Icon";
import "./Footer.css";
import React from "react";

export const Footer = () => {
    const smallLayout = useMediaQuery({ maxWidth: 700 });
    const smallLayout1 = useMediaQuery({ maxWidth: 450 });
    const facebookUrl = 'https://facebook.com/mvboxrecords';
    const twitterUrl = 'https://x.com/mvboxrecords';
    const instagramUrl = 'https://instagram.com/mvboxofficial';

    return (
        <div className="footer" style={smallLayout1 ? {flexDirection: "column-reverse", gap: "24px"} : null}>
            {smallLayout ? (
                <div className="group-section">
                    <div className="text-wrapper">mvboxrecords © 2024</div>
                    <div className="text-wrapper">mvboxrecords@gmail.com</div>
                </div>
            ) : (
                <>
                    <div className="text-wrapper">mvboxrecords © 2024</div>
                    <div className="text-wrapper">mvboxrecords@gmail.com</div>
                </>
            )
            }
            <div className="social-media">
                <Icon iconType={ICONS.FacebookIcon} width="32" height="32"
                    onClick={() => window.open(facebookUrl, '_blank', 'noopener,noreferrer')} />
                <Icon iconType={ICONS.InstagramIcon} width="32" height="32"
                    onClick={() => window.open(instagramUrl, '_blank', 'noopener,noreferrer')} />
                <Icon iconType={ICONS.TwitterIcon} width="32" height="32"
                    onClick={() => window.open(twitterUrl, '_blank', 'noopener,noreferrer')} />
            </div>
        </div>
    );
};