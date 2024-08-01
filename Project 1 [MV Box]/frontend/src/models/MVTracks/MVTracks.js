import "./MVTracks.css";
import { TrackCard } from "../../components/Cards/TrackCard/TrackCard";
import React from "react";
import { MVTracksInfiniteQuery } from "../../queries/requests";
import { Loader } from "../../components/Cards/Loader/Loader";
import { BoxButton } from "../../components/Buttons/BoxButton/BoxButton";

export const MVTracks = ({ header = true }) => {
    const infiniteQuery = MVTracksInfiniteQuery();

    return (
        <div className="mv-tracks">
            {header &&
                <div className="top-section">
                    <div className="text-wrapper">MV Tracks</div>
                </div>
            }
            <div className="tracks">
                {infiniteQuery.isPending && <Loader box={true} />}
                {infiniteQuery.isSuccess &&
                    infiniteQuery.data.pages.map((group, i) => (
                        <React.Fragment key={i}>
                            {group.tracks?.map((item) =>
                                <TrackCard key={item.title} trackInfo={item} />
                            )}
                        </React.Fragment>
                    ))
                }

                {!infiniteQuery.isFetchingNextPage &&
                    !infiniteQuery.isFetching &&
                    infiniteQuery.hasNextPage &&
                    <div className="end-card">
                        <BoxButton onClick={infiniteQuery.fetchNextPage}>Load More</BoxButton>
                    </div>
                }

                {infiniteQuery.isFetchingNextPage &&
                    <div className="end-card">
                        <Loader width="32" height="32" />
                    </div>
                }
            </div>
        </div>
    );
};