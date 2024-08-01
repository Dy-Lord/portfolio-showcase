const host = process.env.REACT_APP_API_HOST;

export const endpoints = {
    topPlaylists: `${host}/public/general/playlists/top_playlists`,
    trackPlaylist: `${host}/public/general/playlists/track_playlist`,
    mvTracks: `${host}/public/general/tracks/mv_tracks`,
    landingStats: `${host}/public/general/info/landing_stats`,
    memberJoin: `${host}/public/general/members/join`,
}