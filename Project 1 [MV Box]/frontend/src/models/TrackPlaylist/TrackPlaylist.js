import React, { useState } from "react";
import "./TrackPlaylist.css";
import { TextInput } from "../../components/Inputs/TextInput/TextInput";
import { BoxButton } from "../../components/Buttons/BoxButton/BoxButton";
import { Loader } from "../../components/Cards/Loader/Loader";
import { TrackPlaylistMutation } from "../../queries/requests";
import Popup from "reactjs-popup";
import { PlaylistTracked } from "../../components/Overlays/PlaylistTracked/PlaylistTracked";

export const TrackPlaylist = () => {
    const [inputValue, setInputValue] = useState("");
    const [invalid, setInvalid] = useState(null);
    const trackPlaylistMutation = TrackPlaylistMutation();
    const [openModal, setOpenModal] = useState(false);
    const [playlist, setPlaylist] = useState(null);

    const handleSubmit = (event) => {
        event.preventDefault();

        if (inputValue && !trackPlaylistMutation.isPending) {
            trackPlaylistMutation.mutate({ playlistUrl: inputValue }, {
                onSuccess: async (response) => {
                    const data = await response.json();
                    setPlaylist(data);
                    setOpenModal(true);
                    setInputValue("");
                    setInvalid(null);
                },
                onError: (error) => {
                    if (error.response.status === 400) {
                        setInvalid("Playlist not found");
                    } else if (error.response.status === 403) {
                        setInvalid("The playlist is already being tracked");
                    }
                }
            });
        }
    };

    return (
        <div className="tracking">
            <Popup 
                open={openModal}
                closeOnDocumentClick 
                onClose={() => setOpenModal(false)}
                modal
            >
                <PlaylistTracked playlistInfo={playlist} onClose={() => setOpenModal(false)}/>
            </Popup>
            <div className="top-section">
                <div className="title">Track my playlist</div>
            </div>
            <form className="track-form" onSubmit={handleSubmit}>
                <TextInput
                    label="Playlist URL"
                    inputValue={inputValue}
                    setInputValue={setInputValue}
                    invalid={invalid}
                />
                <div className="bottom-section">
                    <div className="info">
                        {invalid &&
                            <p className="p invalid">{invalid}</p>
                        }
                        <p className="p">Only spotify playlists are supported</p>
                    </div>
                    <div className="button-section">
                        {trackPlaylistMutation.isPending && <Loader />}
                        <BoxButton>
                            track
                        </BoxButton>
                    </div>
                </div>
            </form>
        </div>
    );
};