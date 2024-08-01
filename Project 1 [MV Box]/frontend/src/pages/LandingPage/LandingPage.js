import "./LandingPage.css";
import { Header } from "../../models/Header/Header";
import React, { useRef } from "react";
import { TopPlaylists } from "../../models/TopPlaylists/TopPlaylists";
import { MVTracks } from "../../models/MVTracks/MVTracks";
import { TrackPlaylist } from "../../models/TrackPlaylist/TrackPlaylist";
import { LandingStats } from "../../models/LandingStats/LandingStats";
import { JoinForm } from "../../models/JoinForm/JoinForm";
import { About } from "../../models/About/About";
import { Footer } from "../../models/Footer/Footer";
import { useMediaQuery } from 'react-responsive';
import { TopPlaylistsMvTracksSwitch } from "../../models/TopPlaylistsMvTracksSwitch/TopPlaylistsMvTracksSwitch";


export const LandingPage = () => {
    const joinFormRef = useRef(null);
    const aboutRef = useRef(null);

    const bigLayout = useMediaQuery({ minWidth: 1288 });
    const mediumLayout = useMediaQuery({ minWidth: 880, maxWidth: 1287 });
    const smallLayout = useMediaQuery({ maxWidth: 879 });

    return (
        <>
            <div className="edge-section">
                <Header aboutRef={aboutRef} joinFormRef={joinFormRef} />
                {bigLayout &&
                    <div className="content-section">
                        <TopPlaylists />
                        <MVTracks />
                        <div className="vertical-section">
                            <TrackPlaylist />
                            <LandingStats />
                        </div>
                    </div>
                }

                {mediumLayout &&
                    <div className="content-section">
                     <TopPlaylistsMvTracksSwitch />
                    <div className="vertical-section">
                        <TrackPlaylist />
                        <LandingStats />
                    </div>
                </div>
                }

                {smallLayout &&
                    <div className="vertical-section" style={{alignItems: "center", gap: "64px"}}>
                        <TopPlaylistsMvTracksSwitch />
                        <LandingStats />
                        <TrackPlaylist />
                    </div>

                }
            </div>
            <div ref={joinFormRef} className="content-section">
                <JoinForm />
            </div>
            <div className="edge-section">
                <div ref={aboutRef} className="content-section">
                    <About />
                </div>
                <Footer />
            </div>
        </>
    );
};