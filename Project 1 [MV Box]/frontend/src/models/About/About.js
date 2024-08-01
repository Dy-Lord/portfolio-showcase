import { useMediaQuery } from "react-responsive";
import "./About.css";
import React from "react";

export const About = () => {
    const smallLayout = useMediaQuery({ maxWidth: 700 });

    return (
        <div className="about">
            <div className="top-section">
                <p className="title">
                    {smallLayout ? "About" : "What the hell is going on here?"}
                </p>
            </div>
            <div className="info">
                <p className="main-text">
                    You&#39;ve reached
                    <span className="accent"> MV Box Playlists </span>
                    page.&nbsp;&nbsp;
                    <br /> <br />
                    Every week we take a snapshot of top 10 playlists <br />
                    and share them among all

                    <span className="accent"> MV Network </span>

                    
                    members. <br /> <br />
                    The position of your playlist depends on two factors: <br />
                    º Number of

                    <span className="accent"> MV Tracks </span>

                    in the playlist
                    <br />
                    º Number of followers
                    <br />
                    <br />
                    <br />
                    The

                    <span className="accent"> MV track </span>

                    
                    list is updated from time to time - so don&#39;t forget <br />
                    to keep an up-to-date list of

                    <span className="accent"> MV tracks </span>

                    
                    in your playlist if you want to stay on top. <br />
                    Join

                    <span className="accent"> MV Box </span>
                    as a curator to be notified when
                    <span className="accent"> MV tracks </span>

                    
                    are updated. <br />
                    <br />
                    To get your playlist in our hangout - just add it to the tracking on this page.
                    <br />
                    It&#39;s absolutely

                    <span className="accent"> free</span>

                    . <br /> <br />
                    If you are an artist and want your tracks to be in

                    <span className="accent"> MV Tracks </span>
                    list - join
                    <span className="accent"> MV Box </span>
                    !
                </p>
            </div>
        </div>
    );
};