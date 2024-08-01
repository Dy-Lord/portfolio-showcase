import "./JoinForm.css";
import React, { useState } from "react";
import { BoxButton } from "../../components/Buttons/BoxButton/BoxButton";
import { RadioCard } from "../../components/Cards/RadioCard/RadioCard";
import { TextInput } from "../../components/Inputs/TextInput/TextInput";
import { Loader } from "../../components/Cards/Loader/Loader";
import { MemberJoinMutation } from "../../queries/requests";
import { NewMember } from "../../components/Overlays/NewMember/NewMember";
import Popup from "reactjs-popup";

export const JoinForm = () => {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [invalid, setInvalid] = useState(null);
    const roles = ["artist", "curator", "fan"];
    const [role, setRole] = useState(roles[0]);
    const joinMutation = MemberJoinMutation();
    const [openModal, setOpenModal] = useState(false);

    const handleSubmit = () => {
        if (name && email && !joinMutation.isPending) {
            joinMutation.mutate({ name, email, memberType: role }, {
                onSuccess: () => {
                    setOpenModal(true);
                    setName("");
                    setEmail("");
                    setInvalid(null);
                },
                onError: (error) => {
                    if (error.response.status === 400) {
                        setInvalid("Invalid email");
                    } else if (error.response.status === 403) {
                        setInvalid("You're already a member of the MV Box network");
                    }
                },
            });
        }
    };

    return (
        <div className="join-form">
            <Popup
                open={openModal}
                closeOnDocumentClick 
                onClose={() => setOpenModal(false)}
                modal
            >
                <NewMember onClose={() => setOpenModal(false)}/>
            </Popup>
            <div className="top-section">
                <div className="text-wrapper">JOIN MV Box</div>
            </div>
            <div className="form">
                <div className="form-section">
                    <TextInput
                        label="Name"
                        placeholder="Jack"
                        inputValue={name}
                        setInputValue={setName}
                    />
                    <TextInput
                        label="Email"
                        placeholder="music@email.com"
                        inputValue={email}
                        setInputValue={setEmail}
                    />
                    <div className="selection-box">
                        {roles.map((item) => 
                        <RadioCard 
                            key={item} 
                            label={item} 
                            active={item === role}
                            onClick={() => setRole(item)} />
                        )}
                    </div>
                </div>
                <div className="button-section">
                    <BoxButton onClick={handleSubmit}>
                        {joinMutation.isPending ? <Loader width="20" height="20"/> : "JOIN"}
                    </BoxButton>
                    {invalid && 
                        <p className="p invalid">{invalid}</p>
                    }
                </div>
            </div>
        </div>
    );
};