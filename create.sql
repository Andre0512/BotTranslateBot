SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


CREATE TABLE bots (
  id int(10) NOT NULL,
  name varchar(64) NOT NULL,
  owner_id int(12) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE languages (
  language_code varchar(5) NOT NULL,
  name varchar(64) NOT NULL,
  local_name varchar(64) NOT NULL,
  flag varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE strings (
  translation_id int(11) NOT NULL,
  string text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE translations (
  id int(12) NOT NULL,
  bot_id int(12) NOT NULL,
  lang_code varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


CREATE TABLE users (
  id int(12) NOT NULL,
  username varchar(64) DEFAULT NULL,
  forename varchar(64) NOT NULL,
  surname varchar(64) DEFAULT NULL,
  lang_code varchar(5) NOT NULL,
  country_code varchar(5) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE bots
  ADD PRIMARY KEY (id),
  ADD KEY owner_id (owner_id);


ALTER TABLE languages
  ADD PRIMARY KEY (language_code),
  ADD UNIQUE KEY language_code (language_code);

  
ALTER TABLE strings
  ADD KEY translation_id (translation_id);


ALTER TABLE translations
  ADD PRIMARY KEY (id),
  ADD KEY bot_id (bot_id),
  ADD KEY lang_id (lang_code),
  ADD KEY lang_id_2 (lang_code),
  ADD KEY bot_id_2 (bot_id);


ALTER TABLE users
  ADD PRIMARY KEY (id),
  ADD UNIQUE KEY id (id),
  ADD KEY lang_code (lang_code);


ALTER TABLE bots
  MODIFY id int(10) NOT NULL AUTO_INCREMENT;


ALTER TABLE translations
  MODIFY id int(12) NOT NULL AUTO_INCREMENT;


ALTER TABLE bots
  ADD CONSTRAINT bots_ibfk_1 FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE;

  
ALTER TABLE strings
  ADD CONSTRAINT strings_ibfk_1 FOREIGN KEY (translation_id) REFERENCES translations (id) ON DELETE CASCADE ON UPDATE CASCADE;

  
ALTER TABLE translations
  ADD CONSTRAINT translations_ibfk_1 FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT translations_ibfk_2 FOREIGN KEY (lang_code) REFERENCES languages (language_code) ON DELETE CASCADE ON UPDATE CASCADE;


ALTER TABLE users
  ADD CONSTRAINT users_ibfk_1 FOREIGN KEY (lang_code) REFERENCES languages (language_code) ON DELETE CASCADE ON UPDATE CASCADE;