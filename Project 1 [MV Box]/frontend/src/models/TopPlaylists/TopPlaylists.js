import "./TopPlaylists.css";
import React from "react";
import { PlaylistCard } from "../../components/Cards/PlaylistCard/PlaylistCard";
import { TopPlaylistsInfiniteQuery } from "../../queries/requests";
import { Loader } from "../../components/Cards/Loader/Loader";
import { BoxButton } from "../../components/Buttons/BoxButton/BoxButton";


export const TopPlaylists = ({ header = true }) => {
    const infiniteQuery = TopPlaylistsInfiniteQuery();

    return (
        <div className="top-playlists">
            {header &&
                <div className="top-section">
                    <div className="text-wrapper-2">Top Playlists</div>
                </div>
            }
            <div className="playlsits">
                {infiniteQuery.isPending && <Loader box={true} />}
                {infiniteQuery.isSuccess &&
                    infiniteQuery.data.pages.map((group, i) => (
                        <React.Fragment key={i}>
                            {group.playlists?.map((item) =>
                                <PlaylistCard key={item.token} playlistInfo={item} />
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