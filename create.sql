SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `bots` (
  `id` int(10) NOT NULL,
  `name` varchar(64) NOT NULL,
  `owner_id` int(12) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `confirmations` (
  `word_id` int(12) NOT NULL,
  `user_id` int(12) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `languages` (
  `language_code` varchar(5) NOT NULL,
  `name` varchar(64) NOT NULL,
  `native_name` varchar(256) NOT NULL,
  `flag` varchar(24) NOT NULL,
  `google` int(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `strings` (
  `id` int(12) NOT NULL,
  `bot_id` int(12) NOT NULL,
  `name` varchar(64) NOT NULL,
  `comment` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `translations` (
  `id` int(12) NOT NULL,
  `bot_id` int(12) NOT NULL,
  `lang_code` varchar(5) NOT NULL,
  `state` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `users` (
  `id` int(12) NOT NULL,
  `username` varchar(64) DEFAULT NULL,
  `forename` varchar(64) NOT NULL,
  `surname` varchar(64) DEFAULT NULL,
  `lang_code` varchar(5) NOT NULL,
  `country_code` varchar(5) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `words` (
  `id` int(12) NOT NULL,
  `value` text NOT NULL,
  `string_id` int(12) NOT NULL,
  `translation_id` int(12) NOT NULL,
  `creator_id` int(12) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `bots`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `owner_id` (`owner_id`);

ALTER TABLE `confirmations`
  ADD KEY `user_id` (`user_id`),
  ADD KEY `word_id` (`word_id`);

ALTER TABLE `languages`
  ADD PRIMARY KEY (`language_code`),
  ADD UNIQUE KEY `language_code` (`language_code`);

ALTER TABLE `strings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `bot_id` (`bot_id`);

ALTER TABLE `translations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lang_code` (`lang_code`),
  ADD KEY `bot_id` (`bot_id`);

ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `lang_code` (`lang_code`);

ALTER TABLE `words`
  ADD PRIMARY KEY (`id`),
  ADD KEY `string_id` (`translation_id`),
  ADD KEY `translator_id` (`creator_id`),
  ADD KEY `translation_id` (`translation_id`),
  ADD KEY `creator_id` (`creator_id`),
  ADD KEY `string_id_2` (`string_id`);


ALTER TABLE `bots`
  MODIFY `id` int(10) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=342;
ALTER TABLE `strings`
  MODIFY `id` int(12) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2140;
ALTER TABLE `translations`
  MODIFY `id` int(12) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;
ALTER TABLE `words`
  MODIFY `id` int(12) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=785;

ALTER TABLE `bots`
  ADD CONSTRAINT `bots_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `confirmations`
  ADD CONSTRAINT `confirmations_ibfk_1` FOREIGN KEY (`word_id`) REFERENCES `words` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `confirmations_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `strings`
  ADD CONSTRAINT `strings_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `translations`
  ADD CONSTRAINT `translations_ibfk_1` FOREIGN KEY (`lang_code`) REFERENCES `languages` (`language_code`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `translations_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`lang_code`) REFERENCES `languages` (`language_code`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `words`
  ADD CONSTRAINT `words_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `words_ibfk_2` FOREIGN KEY (`translation_id`) REFERENCES `translations` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `words_ibfk_3` FOREIGN KEY (`string_id`) REFERENCES `strings` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
