import { useState, useEffect } from 'react';

export const useCountdownTimer = () => {
    const [timeLeft, setTimeLeft] = useState(null);
    const [isActive, setIsActive] = useState(false);

    useEffect(() => {
        let timer;
        if (isActive && timeLeft > 0) {
            timer = setInterval(() => {
                setTimeLeft(prevTime => prevTime - 1);
            }, 1000);
        } else {
            clearInterval(timer);
            setIsActive(false);
        }

        return () => clearInterval(timer);
    }, [isActive, timeLeft]);

    const startTimer = (time) => {
        setTimeLeft(time);
        setIsActive(true);
    };

    const pauseTimer = () => {
        setIsActive(false);
    };

    const resetTimer = () => {
        setTimeLeft(null);
        setIsActive(false);
    };

    return { timeLeft, isActive, startTimer, pauseTimer, resetTimer };
}