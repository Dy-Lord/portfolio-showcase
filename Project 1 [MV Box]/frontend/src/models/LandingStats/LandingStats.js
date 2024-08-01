import "./LandingStats.css";
import React, { useEffect } from "react";
import { InfoCard } from "../../components/Cards/InfoCard/InfoCard";
import { LandingStatsQuery } from "../../queries/requests";
import { useCountdownTimer } from "../../hooks/useCountdownTimer";
import { formatLeftTime } from "../../tools";

export const LandingStats = () => {
    const statsQuery = LandingStatsQuery();
    const { timeLeft, isActive, startTimer, pauseTimer, resetTimer } = useCountdownTimer();

    useEffect(() => {
        if (statsQuery.isSuccess) {
            const now = new Date();
            const nextSnapshotDate = new Date(statsQuery.data.next_snapshot_at * 1000);
            const differenceInSeconds = Math.floor((nextSnapshotDate.getTime() - now.getTime()) / 1000); 
            startTimer(differenceInSeconds);
        }
    }, [statsQuery.isSuccess]);

    return (
        <div className="landing-stats">
            {statsQuery.isSuccess &&
                <>
                    <InfoCard title="Next snapshot of playlists in" content={formatLeftTime(timeLeft)}/>
                    <InfoCard title="Views of this page" content={statsQuery.data.view_count.toLocaleString()}/> 
                    <InfoCard title="Network members" content={statsQuery.data.network_coverage.toLocaleString()}/>
                </>
            }
        </div>
    );
};