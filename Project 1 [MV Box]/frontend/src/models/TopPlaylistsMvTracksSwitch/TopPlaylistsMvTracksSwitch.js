import "./TopPlaylistsMvTracksSwitch.css";
import { useState } from "react";
import { Switch } from "../../components/Buttons/Switch/Switch";
import { TopPlaylists } from "../TopPlaylists/TopPlaylists";
import { MVTracks } from "../MVTracks/MVTracks";

export const TopPlaylistsMvTracksSwitch = () => {
    const [currentOption, setCurrentOption] = useState("Top Playlists");

    const options = [
        {
            name: "Top Playlists",
            onClick: () => setCurrentOption("Top Playlists"),
        },
        {
            name: "MV Tracks",
            onClick: () => setCurrentOption("MV Tracks"),
        },
    ]

    return (
        <div className="composite-component">
            <div className="top-section">
                <Switch options={options} defaultOption="Top Playlists" />
            </div>
            {currentOption === "Top Playlists" &&
                <TopPlaylists header={false} />
            }
            {currentOption === "MV Tracks" &&
                <MVTracks header={false} />
            }
        </div>
    );
};