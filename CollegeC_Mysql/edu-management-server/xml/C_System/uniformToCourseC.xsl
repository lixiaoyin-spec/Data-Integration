<?xml version="1.0" encoding="UTF-8"?>
<!-- 统一集成格式 → C(MySQL) 课程格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Courses>
      <xsl:for-each select="Classes/class">
        <course>
          <Cno><xsl:value-of select="id"/></Cno>
          <Cnm><xsl:value-of select="name"/></Cnm>
          <Ctm><xsl:value-of select="hours"/></Ctm>
          <Cpt><xsl:value-of select="credit"/></Cpt>
          <Tec><xsl:value-of select="teacher"/></Tec>
          <Pla><xsl:value-of select="location"/></Pla>
          <Share><xsl:value-of select="share_flag"/></Share>
        </course>
      </xsl:for-each>
    </Courses>
  </xsl:template>

</xsl:stylesheet>
